from __future__ import annotations

import os
import subprocess
import sys
import threading
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from cli import (
    baixar_mp3,
    buscar_videos,
    extrair_playlist,
    is_valid_playlist_url,
    normalizar_urls,
)


app = FastAPI(title="YouTube MP3 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


InputType = Literal["playlist", "search", "manual"]
ItemStatus = Literal["pending", "downloading", "done", "error"]
JobState = Literal["queued", "running", "completed", "completed_with_errors"]
DEFAULT_AUDIO_QUALITY = "192"


class CollectRequest(BaseModel):
    type: InputType
    value: str = Field(min_length=1)
    limit: int = Field(default=20, ge=1, le=200)


class CollectResponse(BaseModel):
    urls: List[str]
    invalid_count: int = 0
    duplicate_count: int = 0


class DownloadRequest(BaseModel):
    urls: List[str]
    output_path: Optional[str] = None
    output: Optional[str] = None
    archive: str = Field(default="archive.txt")


class DownloadStartResponse(BaseModel):
    job_id: str
    total_urls: int
    invalid_count: int
    duplicate_count: int


class DestinationOption(BaseModel):
    label: str
    path: str


class DestinationsResponse(BaseModel):
    default_output_path: str
    options: List[DestinationOption]


class SelectDirectoryRequest(BaseModel):
    initial_path: Optional[str] = None


class SelectDirectoryResponse(BaseModel):
    selected_path: Optional[str] = None
    canceled: bool = False


class JobItem(BaseModel):
    url: str
    status: ItemStatus = "pending"
    message: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    state: JobState = "queued"
    total: int
    completed: int = 0
    success: int = 0
    errors: int = 0
    progress: int = 0
    started_at: str
    finished_at: Optional[str] = None
    items: List[JobItem]


JOBS: Dict[str, JobStatus] = {}
JOBS_LOCK = threading.Lock()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compute_progress(completed: int, total: int) -> int:
    if total <= 0:
        return 0
    return int((completed / total) * 100)


def resolve_and_validate_output_path(payload: DownloadRequest) -> str:
    candidate = (payload.output_path or payload.output or "").strip()
    if not candidate:
        candidate = os.path.abspath("downloads")

    if payload.output_path and not os.path.isabs(candidate):
        raise HTTPException(status_code=400, detail="`output_path` deve ser um caminho absoluto.")

    try:
        os.makedirs(candidate, exist_ok=True)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Falha ao criar/acessar diretório de saída: {exc}",
        ) from exc

    if not os.path.isdir(candidate):
        raise HTTPException(status_code=400, detail="Caminho de saída inválido: não é diretório.")

    if not os.access(candidate, os.W_OK):
        raise HTTPException(status_code=400, detail="Sem permissão de escrita no diretório de saída.")

    try:
        with tempfile.NamedTemporaryFile(dir=candidate, prefix=".write-check-", delete=True):
            pass
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Diretório de saída não gravável: {exc}",
        ) from exc

    return candidate


def get_destination_options() -> DestinationsResponse:
    project_default = os.path.abspath("downloads")
    home = os.path.expanduser("~")

    candidates = [
        ("Projeto (downloads)", project_default),
        ("Downloads", os.path.join(home, "Downloads")),
        ("Músicas", os.path.join(home, "Music")),
        ("Desktop", os.path.join(home, "Desktop")),
    ]

    options: List[DestinationOption] = []
    seen_paths = set()

    for label, path in candidates:
        normalized = os.path.abspath(path)
        if normalized in seen_paths:
            continue
        seen_paths.add(normalized)
        options.append(DestinationOption(label=label, path=normalized))

    return DestinationsResponse(default_output_path=project_default, options=options)


def open_native_directory_picker(initial_path: Optional[str] = None) -> Optional[str]:
    start_dir = os.path.expanduser("~")
    if initial_path and os.path.isdir(initial_path):
        start_dir = initial_path

    try:
        import tkinter as tk
        from tkinter import filedialog
        root = None
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            selected = filedialog.askdirectory(
                title="Selecionar pasta de destino",
                initialdir=start_dir,
                mustexist=False,
            )
        finally:
            if root is not None:
                try:
                    root.destroy()
                except Exception:
                    pass

        if selected:
            return os.path.abspath(selected)
        return None
    except Exception:
        # Fallback por sistema operacional quando tkinter não está disponível.
        pass

    if sys.platform == "darwin":
        script = (
            'set pickedFolder to choose folder with prompt "Selecionar pasta de destino" '
            f'default location POSIX file "{start_dir}"\n'
            "POSIX path of pickedFolder"
        )
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            # Cancelamento do usuário no macOS normalmente retorna -128.
            if "User canceled" in stderr or "(-128)" in stderr:
                return None
            raise HTTPException(
                status_code=500,
                detail=f"Não foi possível abrir o seletor de pastas (macOS): {stderr or 'erro desconhecido'}",
            )
        selected = (proc.stdout or "").strip()
        return os.path.abspath(selected) if selected else None

    if os.name == "nt":
        ps_script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "$dialog = New-Object System.Windows.Forms.FolderBrowserDialog; "
            '$dialog.Description = "Selecionar pasta de destino"; '
            f'$dialog.SelectedPath = "{start_dir.replace("\\", "\\\\")}"; '
            "if ($dialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) { "
            "Write-Output $dialog.SelectedPath }"
        )
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            raise HTTPException(
                status_code=500,
                detail=f"Não foi possível abrir o seletor de pastas (Windows): {stderr or 'erro desconhecido'}",
            )
        selected = (proc.stdout or "").strip()
        return os.path.abspath(selected) if selected else None

    # Linux: tenta zenity e depois kdialog.
    for cmd in (
        ["zenity", "--file-selection", "--directory", "--title=Selecionar pasta de destino", "--filename", start_dir + "/"],
        ["kdialog", "--getexistingdirectory", start_dir, "Selecionar pasta de destino"],
    ):
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode == 0:
            selected = (proc.stdout or "").strip()
            if selected:
                return os.path.abspath(selected)
        # returncode 1 normalmente é cancelamento em zenity/kdialog.
        if proc.returncode not in (0, 1):
            continue

    raise HTTPException(
        status_code=500,
        detail="Seletor nativo indisponível: instale suporte gráfico (tkinter/zenity/kdialog) ou informe o caminho manualmente.",
    )


def _collect_urls(payload: CollectRequest) -> CollectResponse:
    if payload.type == "playlist":
        if not is_valid_playlist_url(payload.value):
            raise ValueError("URL de playlist inválida. Informe uma URL do YouTube com parâmetro `list`.")
        raw_urls = extrair_playlist(payload.value)
    elif payload.type == "search":
        raw_urls = buscar_videos(payload.value, limite=payload.limit)
    else:
        raw_urls = [line.strip() for line in payload.value.splitlines() if line.strip()]

    normalized, invalid_count, duplicate_count = normalizar_urls(raw_urls)
    return CollectResponse(
        urls=normalized,
        invalid_count=invalid_count,
        duplicate_count=duplicate_count,
    )


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/destinations", response_model=DestinationsResponse)
def destinations() -> DestinationsResponse:
    return get_destination_options()


@app.post("/api/select-directory", response_model=SelectDirectoryResponse)
def select_directory(payload: SelectDirectoryRequest) -> SelectDirectoryResponse:
    selected = open_native_directory_picker(payload.initial_path)
    if not selected:
        return SelectDirectoryResponse(selected_path=None, canceled=True)
    return SelectDirectoryResponse(selected_path=selected, canceled=False)


@app.post("/api/collect", response_model=CollectResponse)
def collect(payload: CollectRequest) -> CollectResponse:
    try:
        response = _collect_urls(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Falha ao coletar URLs: {exc}") from exc

    if not response.urls:
        return response
    return response


def run_download_job(job_id: str, quality: str, output: str, archive: str) -> None:
    with JOBS_LOCK:
        job = JOBS[job_id]
        job.state = "running"

    for item in job.items:
        with JOBS_LOCK:
            item.status = "downloading"
            item.message = None

        try:
            baixar_mp3(item.url, output=output, quality=quality, archive=archive)
            with JOBS_LOCK:
                item.status = "done"
                job.success += 1
                job.completed += 1
                job.progress = compute_progress(job.completed, job.total)
        except Exception as exc:
            with JOBS_LOCK:
                item.status = "error"
                item.message = str(exc)
                job.errors += 1
                job.completed += 1
                job.progress = compute_progress(job.completed, job.total)

    with JOBS_LOCK:
        job.state = "completed_with_errors" if job.errors else "completed"
        job.progress = 100
        job.finished_at = utc_now_iso()


@app.post("/api/download", response_model=DownloadStartResponse)
def start_download(payload: DownloadRequest) -> DownloadStartResponse:
    output_path = resolve_and_validate_output_path(payload)

    normalized, invalid_count, duplicate_count = normalizar_urls(payload.urls)
    if not normalized:
        raise HTTPException(status_code=400, detail="Nenhuma URL válida para download.")

    job_id = str(uuid.uuid4())
    items = [JobItem(url=url) for url in normalized]
    job = JobStatus(
        job_id=job_id,
        total=len(items),
        started_at=utc_now_iso(),
        items=items,
    )

    with JOBS_LOCK:
        JOBS[job_id] = job

    thread = threading.Thread(
        target=run_download_job,
        args=(job_id, DEFAULT_AUDIO_QUALITY, output_path, payload.archive),
        daemon=True,
    )
    thread.start()

    return DownloadStartResponse(
        job_id=job_id,
        total_urls=len(normalized),
        invalid_count=invalid_count,
        duplicate_count=duplicate_count,
    )


@app.get("/api/status/{job_id}", response_model=JobStatus)
def get_status(job_id: str) -> JobStatus:
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job não encontrado.")
        return job


@app.get("/api/status", response_model=JobStatus)
def get_status_query(job_id: str = Query(..., description="ID do job de download")) -> JobStatus:
    return get_status(job_id)
