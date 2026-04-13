export default function StatCard({ label, value, sub, icon: Icon, color = "blue", loading }) {
  const colors = {
    blue:  "text-blue-400  bg-blue-400/10",
    green: "text-green-400 bg-green-400/10",
    red:   "text-red-400   bg-red-400/10",
    amber: "text-amber-400 bg-amber-400/10",
    purple:"text-purple-400 bg-purple-400/10",
  };

  return (
    <div className="card flex items-start gap-4">
      {Icon && (
        <div className={`p-2.5 rounded-lg shrink-0 ${colors[color]}`}>
          <Icon size={20} />
        </div>
      )}
      <div className="min-w-0">
        <p className="text-gray-400 text-xs uppercase tracking-wide mb-1">{label}</p>
        {loading
          ? <div className="h-7 w-20 bg-gray-800 rounded animate-pulse" />
          : <p className="text-2xl font-bold text-white">{value ?? "—"}</p>
        }
        {sub && <p className="text-gray-500 text-xs mt-1 truncate">{sub}</p>}
      </div>
    </div>
  );
}
