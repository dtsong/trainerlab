"use client";

interface StatCardProps {
  label: string;
  value: string | number;
  detail?: string;
}

export function StatCard({ label, value, detail }: StatCardProps) {
  return (
    <div className="rounded border border-zinc-800 bg-zinc-900/50 px-4 py-3">
      <div className="font-mono text-xs uppercase tracking-wider text-zinc-500">
        {label}
      </div>
      <div className="mt-1 font-mono text-2xl font-semibold text-zinc-100">
        {typeof value === "number" ? value.toLocaleString() : value}
      </div>
      {detail && (
        <div className="mt-0.5 font-mono text-xs text-zinc-500">{detail}</div>
      )}
    </div>
  );
}
