const variants = {
  ALLOWED:      "bg-green-500/15 text-green-400 border-green-500/20",
  BLOCKED:      "bg-red-500/15   text-red-400   border-red-500/20",
  active:       "bg-green-500/15 text-green-400 border-green-500/20",
  unregistered: "bg-amber-500/15 text-amber-400 border-amber-500/20",
  missing:      "bg-red-500/15   text-red-400   border-red-500/20",
  local:        "bg-blue-500/15  text-blue-400  border-blue-500/20",
  clawhub:      "bg-purple-500/15 text-purple-400 border-purple-500/20",
};

export default function Badge({ label, variant }) {
  const cls = variants[variant] ?? "bg-gray-500/15 text-gray-400 border-gray-500/20";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      {label}
    </span>
  );
}
