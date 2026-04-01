import { LinkItem } from "../lib/types";

type Props = {
  links: LinkItem[];
  onToggle: (id: string) => void;
  onRemove: (id: string) => void;
  onSelectAll: () => void;
  onClear: () => void;
};

export function LinksList({ links, onToggle, onRemove, onSelectAll, onClear }: Props) {
  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onSelectAll}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-primary/70"
        >
          Selecionar todos
        </button>
        <button
          type="button"
          onClick={onClear}
          className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-rose-400 hover:text-rose-600"
        >
          Limpar lista
        </button>
      </div>

      <div className="max-h-72 space-y-2 overflow-auto pr-1">
        {links.length === 0 && (
          <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
            Nenhum link carregado.
          </p>
        )}

        {links.map((item) => (
          <div
            key={item.id}
            className="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3"
          >
            <label className="flex min-w-0 flex-1 items-start gap-3">
              <input
                type="checkbox"
                checked={item.selected}
                onChange={() => onToggle(item.id)}
                className="mt-1 h-4 w-4 accent-primary"
              />
              <span className="break-all text-xs text-slate-700">{item.url}</span>
            </label>

            <button
              type="button"
              onClick={() => onRemove(item.id)}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:border-rose-400 hover:text-rose-600"
            >
              remover
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
