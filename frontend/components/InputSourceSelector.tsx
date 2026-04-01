import { SourceType } from "../lib/types";

type Props = {
  value: SourceType;
  onChange: (value: SourceType) => void;
};

const options: Array<{ label: string; value: SourceType }> = [
  { label: "Playlist", value: "playlist" },
  { label: "Busca", value: "search" },
  { label: "Lista manual", value: "manual" }
];

export function InputSourceSelector({ value, onChange }: Props) {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          onClick={() => onChange(option.value)}
          className={`rounded-xl border px-4 py-2 text-sm font-semibold transition ${
            option.value === value
              ? "border-primary bg-primary text-white"
              : "border-slate-300 bg-white text-slate-700 hover:border-primary/60"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
