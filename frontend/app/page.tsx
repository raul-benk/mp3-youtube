"use client";

import { useEffect, useMemo, useState } from "react";
import { DownloadControls } from "../components/DownloadControls";
import { InputForm } from "../components/InputForm";
import { InputSourceSelector } from "../components/InputSourceSelector";
import { LinksList } from "../components/LinksList";
import { StatusList } from "../components/StatusList";
import {
  CollectResponse,
  DestinationOption,
  DestinationsResponse,
  DownloadResponse,
  JobStatus,
  LinkItem,
  SelectDirectoryResponse,
  SourceType
} from "../lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

function isLikelyPlaylistUrl(value: string): boolean {
  try {
    const parsed = new URL(value.trim());
    const host = parsed.hostname.toLowerCase();
    const validHost =
      host === "youtube.com" ||
      host === "www.youtube.com" ||
      host === "m.youtube.com" ||
      host === "music.youtube.com";
    if (!validHost) return false;
    return Boolean(parsed.searchParams.get("list")?.trim());
  } catch {
    return false;
  }
}

function isAbsolutePath(value: string): boolean {
  const normalized = value.trim();
  if (!normalized) return true;
  if (normalized.startsWith("/")) return true;
  return /^[a-zA-Z]:\\/.test(normalized);
}

function makeLinkItems(urls: string[]): LinkItem[] {
  return urls.map((url, index) => ({
    id: `${url}-${index}`,
    url,
    selected: true
  }));
}

export default function HomePage() {
  const [sourceType, setSourceType] = useState<SourceType>("playlist");
  const [playlistValue, setPlaylistValue] = useState("");
  const [searchValue, setSearchValue] = useState("");
  const [manualValue, setManualValue] = useState("");
  const [searchLimit, setSearchLimit] = useState(20);

  const [outputPath, setOutputPath] = useState("");
  const [destinationOptions, setDestinationOptions] = useState<DestinationOption[]>([]);

  const [links, setLinks] = useState<LinkItem[]>([]);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);

  const [loadingCollect, setLoadingCollect] = useState(false);
  const [loadingDownload, setLoadingDownload] = useState(false);
  const [loadingDestinations, setLoadingDestinations] = useState(true);
  const [loadingBrowseDirectory, setLoadingBrowseDirectory] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [feedbackMessage, setFeedbackMessage] = useState("");

  const selectedCount = useMemo(() => links.filter((item) => item.selected).length, [links]);

  function setSearchLimitSafe(value: number) {
    if (!Number.isFinite(value)) {
      setSearchLimit(20);
      return;
    }
    const clamped = Math.max(1, Math.min(200, Math.trunc(value)));
    setSearchLimit(clamped);
  }

  async function parseError(response: Response): Promise<string> {
    try {
      const data = await response.json();
      return data.detail || "Falha inesperada.";
    } catch {
      return "Falha inesperada.";
    }
  }

  useEffect(() => {
    let active = true;

    async function loadDestinations() {
      setLoadingDestinations(true);
      try {
        const response = await fetch(`${API_BASE}/api/destinations`);
        if (!response.ok) {
          throw new Error(await parseError(response));
        }

        const data = (await response.json()) as DestinationsResponse;
        if (!active) return;

        setDestinationOptions(data.options);
        if (!outputPath.trim()) {
          setOutputPath(data.default_output_path);
        }
      } catch (error) {
        if (!active) return;
        setErrorMessage(
          error instanceof Error
            ? `Não foi possível carregar destinos sugeridos: ${error.message}`
            : "Não foi possível carregar destinos sugeridos."
        );
      } finally {
        if (active) {
          setLoadingDestinations(false);
        }
      }
    }

    loadDestinations();
    return () => {
      active = false;
    };
  }, []);

  async function handleCollect() {
    setErrorMessage("");
    setFeedbackMessage("");
    setLoadingCollect(true);

    const payload: { type: SourceType; value: string; limit: number } = {
      type: sourceType,
      value: "",
      limit: searchLimit
    };

    if (sourceType === "playlist") {
      if (!playlistValue.trim()) {
        setLoadingCollect(false);
        setErrorMessage("Informe a URL da playlist.");
        return;
      }
      if (!isLikelyPlaylistUrl(playlistValue)) {
        setLoadingCollect(false);
        setErrorMessage("URL de playlist inválida. Use uma URL do YouTube com parâmetro list.");
        return;
      }
      payload.value = playlistValue.trim();
    }

    if (sourceType === "search") {
      if (!searchValue.trim()) {
        setLoadingCollect(false);
        setErrorMessage("Informe um termo de busca.");
        return;
      }
      payload.value = searchValue.trim();
    }

    if (sourceType === "manual") {
      if (!manualValue.trim()) {
        setLoadingCollect(false);
        setErrorMessage("Cole ao menos uma URL na lista manual.");
        return;
      }
      payload.value = manualValue.trim();
    }

    try {
      const response = await fetch(`${API_BASE}/api/collect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(await parseError(response));
      }

      const data = (await response.json()) as CollectResponse;
      setLinks(makeLinkItems(data.urls));
      setStatus(null);
      setJobId(null);

      if (data.urls.length === 0) {
        setFeedbackMessage("Nenhuma URL válida encontrada.");
      } else {
        setFeedbackMessage(
          `Lista gerada com ${data.urls.length} URL(s). Inválidas: ${data.invalid_count}, duplicadas: ${data.duplicate_count}.`
        );
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Erro ao coletar links.");
    } finally {
      setLoadingCollect(false);
    }
  }

  function toggleLink(id: string) {
    setLinks((prev) => prev.map((item) => (item.id === id ? { ...item, selected: !item.selected } : item)));
  }

  function removeLink(id: string) {
    setLinks((prev) => prev.filter((item) => item.id !== id));
  }

  function clearLinks() {
    setLinks([]);
  }

  function selectAllLinks() {
    setLinks((prev) => prev.map((item) => ({ ...item, selected: true })));
  }

  async function handleDownload() {
    setErrorMessage("");
    setFeedbackMessage("");

    const selectedUrls = links.filter((item) => item.selected).map((item) => item.url);
    if (selectedUrls.length === 0) {
      setErrorMessage("Selecione pelo menos 1 URL para baixar.");
      return;
    }
    if (!isAbsolutePath(outputPath)) {
      setErrorMessage("Destino inválido. Informe um caminho absoluto (ex.: /Volumes/PENDRIVE/musicas).");
      return;
    }

    setLoadingDownload(true);

    try {
      const response = await fetch(`${API_BASE}/api/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          urls: selectedUrls,
          output_path: outputPath.trim() || undefined
        })
      });

      if (!response.ok) {
        throw new Error(await parseError(response));
      }

      const data = (await response.json()) as DownloadResponse;
      setJobId(data.job_id);
      setFeedbackMessage(
        `Download iniciado para ${data.total_urls} URL(s). Inválidas: ${data.invalid_count}, duplicadas: ${data.duplicate_count}.`
      );
    } catch (error) {
      setLoadingDownload(false);
      setErrorMessage(error instanceof Error ? error.message : "Erro ao iniciar download.");
    }
  }

  async function handleBrowseDirectory() {
    setErrorMessage("");
    setLoadingBrowseDirectory(true);
    try {
      const response = await fetch(`${API_BASE}/api/select-directory`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ initial_path: outputPath.trim() || undefined })
      });

      if (!response.ok) {
        throw new Error(await parseError(response));
      }

      const data = (await response.json()) as SelectDirectoryResponse;
      if (data.canceled) {
        return;
      }

      if (data.selected_path) {
        setOutputPath(data.selected_path);
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Erro ao abrir seletor de pastas.");
    } finally {
      setLoadingBrowseDirectory(false);
    }
  }

  useEffect(() => {
    if (!jobId) return;

    let active = true;
    const timer = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE}/api/status/${jobId}`);
        if (!response.ok) {
          throw new Error(await parseError(response));
        }
        const data = (await response.json()) as JobStatus;
        if (!active) return;

        setStatus(data);

        if (data.state === "completed" || data.state === "completed_with_errors") {
          setLoadingDownload(false);
          clearInterval(timer);
        }
      } catch (error) {
        if (!active) return;
        setLoadingDownload(false);
        setErrorMessage(error instanceof Error ? error.message : "Erro ao consultar status.");
        clearInterval(timer);
      }
    }, 1500);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [jobId]);

  return (
    <main className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:py-12">
      <header className="mb-6 rounded-2xl border border-slate-200 bg-card p-6 shadow-card">
        <p className="font-mono text-xs uppercase tracking-[0.2em] text-primary">MVP Web</p>
        <h1 className="mt-2 font-display text-3xl font-bold text-slate-900">YouTube MP3 Batch Downloader</h1>
        <p className="mt-2 text-sm text-slate-600">
          Colete URLs por playlist, busca ou lista manual, revise links e acompanhe o processamento em tempo real.
        </p>
      </header>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-card p-5 shadow-card">
          <h2 className="font-display text-xl font-semibold text-slate-900">1. Entrada de Dados</h2>
          <InputSourceSelector value={sourceType} onChange={setSourceType} />
          <InputForm
            sourceType={sourceType}
            playlistValue={playlistValue}
            searchValue={searchValue}
            manualValue={manualValue}
            searchLimit={searchLimit}
            onPlaylistValueChange={setPlaylistValue}
            onSearchValueChange={setSearchValue}
            onManualValueChange={setManualValue}
            onSearchLimitChange={setSearchLimitSafe}
            onSubmit={handleCollect}
            loading={loadingCollect}
            submitLabel="Buscar músicas"
          />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-card p-5 shadow-card">
          <h2 className="font-display text-xl font-semibold text-slate-900">2. Lista de Links</h2>
          <p className="mb-3 text-xs text-slate-500">
            {links.length} link(s) carregado(s), {selectedCount} selecionado(s).
          </p>
          <LinksList
            links={links}
            onToggle={toggleLink}
            onRemove={removeLink}
            onSelectAll={selectAllLinks}
            onClear={clearLinks}
          />
        </div>
      </section>

      <section className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-card p-5 shadow-card">
          <h2 className="mb-3 font-display text-xl font-semibold text-slate-900">3. Download</h2>
          <p className="mb-3 text-xs text-slate-500">
            Qualidade fixa: MP3 192 kbps (padrão recomendado).
          </p>
          <DownloadControls
            outputPath={outputPath}
            destinationOptions={destinationOptions}
            selectedCount={selectedCount}
            loading={loadingDownload || loadingDestinations}
            browseLoading={loadingBrowseDirectory}
            onPickDestination={setOutputPath}
            onOutputPathChange={setOutputPath}
            onBrowseDirectory={handleBrowseDirectory}
            onDownload={handleDownload}
          />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-card p-5 shadow-card">
          <h2 className="mb-3 font-display text-xl font-semibold text-slate-900">4. Status</h2>
          <StatusList status={status} />
        </div>
      </section>

      <section className="mt-4 space-y-2">
        {feedbackMessage && (
          <p className="rounded-xl border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
            {feedbackMessage}
          </p>
        )}
        {errorMessage && (
          <p className="rounded-xl border border-rose-300 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            {errorMessage}
          </p>
        )}
      </section>
    </main>
  );
}
