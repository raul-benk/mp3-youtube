import { SourceType } from "../lib/types";

type Props = {
  sourceType: SourceType;
  playlistValue: string;
  searchValue: string;
  manualValue: string;
  searchLimit: number;
  onPlaylistValueChange: (value: string) => void;
  onSearchValueChange: (value: string) => void;
  onManualValueChange: (value: string) => void;
  onSearchLimitChange: (value: number) => void;
  onSubmit: () => void;
  loading: boolean;
  submitLabel?: string;
};

export function InputForm({
  sourceType,
  playlistValue,
  searchValue,
  manualValue,
  searchLimit,
  onPlaylistValueChange,
  onSearchValueChange,
  onManualValueChange,
  onSearchLimitChange,
  onSubmit,
  loading,
  submitLabel = "Gerar lista"
}: Props) {
  return (
    <div className="mt-4 space-y-3">
      {sourceType === "playlist" && (
        <input
          type="text"
          value={playlistValue}
          onChange={(event) => onPlaylistValueChange(event.target.value)}
          placeholder="URL da playlist"
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
        />
      )}

      {sourceType === "search" && (
        <div className="grid gap-3 sm:grid-cols-3">
          <input
            type="text"
            value={searchValue}
            onChange={(event) => onSearchValueChange(event.target.value)}
            placeholder="Artista / termo"
            className="sm:col-span-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
          />
          <input
            type="number"
            min={1}
            max={200}
            value={searchLimit}
            onChange={(event) => onSearchLimitChange(Number(event.target.value))}
            className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
          />
        </div>
      )}

      {sourceType === "manual" && (
        <textarea
          value={manualValue}
          onChange={(event) => onManualValueChange(event.target.value)}
          placeholder="Cole uma URL por linha"
          rows={6}
          className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
        />
      )}

      <button
        type="button"
        onClick={onSubmit}
        disabled={loading}
        className="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Buscando..." : submitLabel}
      </button>
    </div>
  );
}
