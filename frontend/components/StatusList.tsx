import { JobStatus } from "../lib/types";

type Props = {
  status: JobStatus | null;
};

function statusBadge(kind: string): string {
  if (kind === "downloading") return "⏳";
  if (kind === "done") return "✅";
  if (kind === "error") return "❌";
  return "•";
}

export function StatusList({ status }: Props) {
  if (!status) {
    return (
      <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500">
        Nenhum download em execução.
      </p>
    );
  }

  const progress = status.progress;

  return (
    <div className="space-y-3">
      <div className="rounded-xl border border-slate-200 bg-white p-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600">
          <span>Job: {status.job_id}</span>
          <span>Estado: {status.state}</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-200">
          <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-xs text-slate-600">
          {status.completed}/{status.total} concluídos • {status.success} sucesso • {status.errors} erro
        </p>
      </div>

      <div className="max-h-72 space-y-2 overflow-auto pr-1">
        {status.items.map((item, index) => (
          <div
            key={`${item.url}-${index}`}
            className="rounded-xl border border-slate-200 bg-white p-3 text-xs"
          >
            <p className="break-all text-slate-700">
              {statusBadge(item.status)} {item.url}
            </p>
            {item.message && <p className="mt-1 text-rose-600">{item.message}</p>}
          </div>
        ))}
      </div>
    </div>
  );
}
