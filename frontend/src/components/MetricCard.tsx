interface Props {
  label: string;
  value: string;
  tone?: "mint" | "ocean" | "amber" | "rose";
}

const tones = {
  mint: "border-mint/30 bg-teal-50 text-mint",
  ocean: "border-ocean/30 bg-cyan-50 text-ocean",
  amber: "border-amber/30 bg-amber-50 text-amber",
  rose: "border-rose/30 bg-rose-50 text-rose"
};

export function MetricCard({ label, value, tone = "mint" }: Props) {
  return (
    <div className={`rounded border p-4 ${tones[tone]}`}>
      <p className="text-sm font-medium opacity-80">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}
