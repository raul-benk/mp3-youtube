import argparse
import os
import re
import sys
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlparse


YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
}
QUALITY_RE = re.compile(r"^\d{2,3}$")
VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def get_yt_dlp():
    try:
        import yt_dlp

        return yt_dlp
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Dependência ausente: instale com `pip install yt-dlp` para realizar coletas e downloads."
        ) from exc


def parse_quality(value: str) -> str:
    normalized = value.strip()
    if not QUALITY_RE.match(normalized):
        raise argparse.ArgumentTypeError("Qualidade deve ser um número entre 64 e 320 (ex.: 192).")

    bitrate = int(normalized)
    if bitrate < 64 or bitrate > 320:
        raise argparse.ArgumentTypeError("Qualidade deve estar entre 64 e 320 kbps.")

    return str(bitrate)


def parse_limit(value: str) -> int:
    try:
        limite = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Limite deve ser um número inteiro positivo.") from exc

    if limite <= 0:
        raise argparse.ArgumentTypeError("Limite deve ser maior que zero.")

    return limite


def is_valid_playlist_url(url: str) -> bool:
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    host = parsed.netloc.lower()
    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        return False

    playlist_id = parse_qs(parsed.query).get("list", [""])[0].strip()
    return bool(playlist_id)


def extract_playlist_id(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None

    if parsed.scheme not in {"http", "https"}:
        return None

    host = parsed.netloc.lower()
    if host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        return None

    playlist_id = parse_qs(parsed.query).get("list", [""])[0].strip()
    return playlist_id or None


def canonical_playlist_url(url: str) -> Optional[str]:
    playlist_id = extract_playlist_id(url)
    if not playlist_id:
        return None
    return f"https://www.youtube.com/playlist?list={playlist_id}"


def normalize_video_id(value: str) -> Optional[str]:
    candidate = value.strip()
    if VIDEO_ID_RE.fullmatch(candidate):
        return candidate
    return None


def extract_video_id_from_url(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None

    if parsed.scheme not in {"http", "https"}:
        return None
    if parsed.netloc.lower() not in YOUTUBE_HOSTS:
        return None

    host = parsed.netloc.lower()
    if host.endswith("youtu.be"):
        short_id = parsed.path.lstrip("/").split("/")[0]
        return normalize_video_id(short_id)

    if parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [""])[0]
        return normalize_video_id(video_id)

    if parsed.path.startswith("/shorts/"):
        short_path = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
        return normalize_video_id(short_path)

    if parsed.path.startswith("/live/"):
        live_path = parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else ""
        return normalize_video_id(live_path)

    return None


def canonical_url_from_video_id(video_id: str) -> Optional[str]:
    normalized = normalize_video_id(video_id)
    if not normalized:
        return None
    return f"https://www.youtube.com/watch?v={normalized}"


def canonicalize_url(url: str) -> Optional[str]:
    video_id = extract_video_id_from_url(url)
    if not video_id:
        return None
    return canonical_url_from_video_id(video_id)


def carregar_urls_arquivo(path: str) -> List[str]:
    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if line and not line.startswith("#"):
                urls.append(line)
    return urls


def extrair_playlist(url: str) -> List[str]:
    playlist_url = canonical_playlist_url(url)
    if not playlist_url:
        raise ValueError("URL de playlist inválida. Use uma URL do YouTube contendo o parâmetro `list`.")

    yt_dlp = get_yt_dlp()
    ydl_opts = {"extract_flat": True, "quiet": True, "ignoreerrors": True}
    urls: List[str] = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)

    if not result:
        return urls

    entries = result.get("entries", []) if isinstance(result, dict) else []
    for entry in entries:
        if not entry:
            continue

        video_id = normalize_video_id(str(entry.get("id", "")))
        if video_id:
            urls.append(f"https://www.youtube.com/watch?v={video_id}")
            continue

        candidate_url = entry.get("webpage_url") or entry.get("url")
        if candidate_url:
            canonical = canonicalize_url(str(candidate_url))
            if canonical:
                urls.append(canonical)

    if urls:
        return urls

    # Fallback: tenta extração completa quando o modo flat retorna vazio.
    ydl_opts_fallback = {"quiet": True, "ignoreerrors": True}
    with yt_dlp.YoutubeDL(ydl_opts_fallback) as ydl:
        result_full = ydl.extract_info(playlist_url, download=False)

    entries_full = result_full.get("entries", []) if isinstance(result_full, dict) else []
    for entry in entries_full:
        if not entry:
            continue

        video_id = normalize_video_id(str(entry.get("id", "")))
        if video_id:
            urls.append(f"https://www.youtube.com/watch?v={video_id}")
            continue

        candidate_url = entry.get("webpage_url") or entry.get("url")
        if candidate_url:
            canonical = canonicalize_url(str(candidate_url))
            if canonical:
                urls.append(canonical)

    return urls


def buscar_videos(query: str, limite: int = 20) -> List[str]:
    yt_dlp = get_yt_dlp()
    ydl_opts = {"quiet": True, "ignoreerrors": True}
    urls: List[str] = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        resultados = ydl.extract_info(f"ytsearch{limite}:{query}", download=False)

    if not resultados:
        return urls

    for entry in resultados.get("entries", []):
        if not entry:
            continue

        video_id = normalize_video_id(str(entry.get("id", "")))
        if video_id:
            urls.append(f"https://www.youtube.com/watch?v={video_id}")
            continue

        candidate_url = entry.get("webpage_url") or entry.get("url")
        if candidate_url:
            canonical = canonicalize_url(str(candidate_url))
            if canonical:
                urls.append(canonical)

    return urls


def normalizar_urls(urls: List[str]) -> Tuple[List[str], int, int]:
    normalizadas: List[str] = []
    vistos = set()
    invalidas = 0
    duplicadas = 0

    for url in urls:
        if not url:
            continue

        canonical = canonicalize_url(url)
        if not canonical:
            invalidas += 1
            continue

        if canonical in vistos:
            duplicadas += 1
            continue

        vistos.add(canonical)
        normalizadas.append(canonical)

    return normalizadas, invalidas, duplicadas


def salvar_links(urls: List[str], path: str = "links.txt") -> None:
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        for url in urls:
            file.write(url + "\n")


def baixar_mp3(url: str, output: str, quality: str, archive: str) -> None:
    yt_dlp = get_yt_dlp()

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output, "%(title).180B [%(id)s].%(ext)s"),
        "download_archive": archive,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        "quiet": False,
        "no_warnings": False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def processar_urls(urls_validas: List[str], output: str, quality: str, archive: str) -> int:
    os.makedirs(output, exist_ok=True)

    if archive:
        archive_dir = os.path.dirname(os.path.abspath(archive))
        os.makedirs(archive_dir, exist_ok=True)

    if not urls_validas:
        print("[INFO] Nenhuma URL válida encontrada.")
        return 0

    total = len(urls_validas)
    sucesso = 0
    falhas = 0

    print(f"[INFO] Iniciando lote com {total} URL(s) válida(s).")

    for idx, url in enumerate(urls_validas, start=1):
        print(f"[INFO] ({idx}/{total}) Baixando: {url}")
        try:
            baixar_mp3(url, output, quality, archive)
            sucesso += 1
            print(f"[OK] Download finalizado: {url}")
        except Exception as exc:
            falhas += 1
            print(f"[ERRO] Falha ao baixar {url}: {exc}")

    print("\n[RESUMO]")
    print(f"[RESUMO] Sucesso: {sucesso}")
    print(f"[RESUMO] Falhas: {falhas}")

    return 0 if falhas == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Downloader em lote de MP3 do YouTube")

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--file",
        "--input",
        dest="file",
        help="Arquivo com lista de URLs (compatível com --input)",
    )
    source_group.add_argument("--playlist", help="URL da playlist do YouTube")
    source_group.add_argument("--search", help='Busca por termo (ex.: "Linkin Park")')

    parser.add_argument("--limit", default=20, type=parse_limit, help="Limite da busca no modo --search")
    parser.add_argument("--output", default="downloads", help="Pasta de saída (default: downloads)")
    parser.add_argument(
        "--quality",
        default="192",
        type=parse_quality,
        help="Qualidade do MP3 em kbps, de 64 a 320 (default: 192)",
    )
    parser.add_argument(
        "--archive",
        default="archive.txt",
        help="Arquivo de controle para evitar downloads duplicados (default: archive.txt)",
    )
    parser.add_argument(
        "--save-links",
        nargs="?",
        const="links.txt",
        default=None,
        help="Salva os links normalizados em arquivo (default: links.txt)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.playlist:
            print(f"[INFO] Coletando vídeos da playlist: {args.playlist}")
            urls_coletadas = extrair_playlist(args.playlist)
            if not urls_coletadas:
                print("[WARN] Playlist vazia ou sem vídeos válidos.")
        elif args.search:
            print(f"[INFO] Buscando vídeos para: {args.search} (limite={args.limit})")
            urls_coletadas = buscar_videos(args.search, limite=args.limit)
            if not urls_coletadas:
                print("[WARN] Busca sem resultados.")
        else:
            if not os.path.isfile(args.file):
                print(f"[ERRO] Arquivo de entrada não encontrado: {args.file}")
                return 2
            urls_coletadas = carregar_urls_arquivo(args.file)
            print(f"[INFO] URLs carregadas do arquivo: {len(urls_coletadas)}")
    except Exception as exc:
        origem = "--playlist" if args.playlist else "--search" if args.search else "--file"
        print(f"[ERRO] Falha ao processar {origem}: {exc}")
        return 2

    urls_normalizadas, invalidas, duplicadas = normalizar_urls(urls_coletadas)

    if invalidas:
        print(f"[WARN] URLs inválidas ignoradas: {invalidas}")
    if duplicadas:
        print(f"[INFO] URLs duplicadas removidas: {duplicadas}")

    if args.save_links:
        salvar_links(urls_normalizadas, args.save_links)
        print(f"[INFO] Links normalizados salvos em: {args.save_links}")

    return processar_urls(urls_normalizadas, args.output, args.quality, args.archive)


if __name__ == "__main__":
    sys.exit(main())
