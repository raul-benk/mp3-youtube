import { DestinationOption } from "../lib/types";

type Props = {
  outputPath: string;
  destinationOptions: DestinationOption[];
  selectedCount: number;
  loading: boolean;
  browseLoading: boolean;
  onPickDestination: (value: string) => void;
  onOutputPathChange: (value: string) => void;
  onBrowseDirectory: () => void;
  onDownload: () => void;
};

export function DownloadControls({
  outputPath,
  destinationOptions,
  selectedCount,
  loading,
  browseLoading,
  onPickDestination,
  onOutputPathChange,
  onBrowseDirectory,
  onDownload
}: Props) {
  return (
    <div className="space-y-3">
      <div className="grid gap-3">
        <button
          type="button"
          onClick={onBrowseDirectory}
          disabled={browseLoading}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-primary/70 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {browseLoading ? "Abrindo explorador..." : "Selecionar pasta"}
        </button>

        <select
          value=""
          onChange={(event) => {
            if (event.target.value) {
              onPickDestination(event.target.value);
            }
          }}
          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-primary"
        >
          <option value="">Selecionar destino sugerido...</option>
          {destinationOptions.map((option) => (
            <option key={option.path} value={option.path}>
              {option.label}: {option.path}
            </option>
          ))}
        </select>

        <input
          type="text"
          value={outputPath}
          onChange={(event) => onOutputPathChange(event.target.value)}
          placeholder="Destino final (caminho absoluto)"
          className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-primary"
        />
      </div>

      <button
        type="button"
        onClick={onDownload}
        disabled={loading || selectedCount === 0}
        className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {loading ? "Baixando..." : `Baixar todas (${selectedCount})`}
      </button>
    </div>
  );
}
