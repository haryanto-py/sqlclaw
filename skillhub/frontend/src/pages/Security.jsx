import { useEffect, useState } from "react";
import {
  PieChart, Pie, Cell, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer,
} from "recharts";
import { ShieldCheck, ShieldAlert, ShieldX } from "lucide-react";
import StatCard  from "../components/StatCard";
import Badge     from "../components/Badge";
import { api }  from "../api/client";

const PIE_COLORS = ["#22c55e", "#ef4444"];

export default function Security() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    api.security()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const pieData = data
    ? [
        { name: "Allowed", value: data.allowed },
        { name: "Blocked", value: data.blocked },
      ]
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Security</h1>
        <p className="text-gray-400 text-sm mt-1">Query validator stats and blocked attempt history</p>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Queries"   value={data?.total?.toLocaleString()}   icon={ShieldCheck} color="blue"  loading={loading} />
        <StatCard label="Allowed"         value={data?.allowed?.toLocaleString()} icon={ShieldCheck} color="green" loading={loading} />
        <StatCard label="Blocked"         value={data?.blocked?.toLocaleString()} icon={ShieldX}     color="red"   loading={loading} />
        <StatCard
          label="Block Rate"
          value={data ? `${(data.block_rate * 100).toFixed(1)}%` : null}
          icon={ShieldAlert}
          color="amber"
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Pie chart */}
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-4">Allowed vs Blocked</h2>
          {loading
            ? <div className="h-48 bg-gray-800 rounded animate-pulse" />
            : pieData.every((d) => d.value === 0)
              ? <p className="text-gray-600 text-sm py-12 text-center">No queries logged yet.</p>
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} dataKey="value" cx="50%" cy="50%" outerRadius={80} label>
                      {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                      formatter={(v) => [v.toLocaleString(), ""]}
                    />
                    <Legend wrapperStyle={{ color: "#9ca3af", fontSize: 12 }} />
                  </PieChart>
                </ResponsiveContainer>
              )
          }
        </div>

        {/* Top blocked patterns */}
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-4">Top Blocked Patterns</h2>
          {loading
            ? <div className="h-48 bg-gray-800 rounded animate-pulse" />
            : (data?.top_blocked_patterns ?? []).length === 0
              ? <p className="text-gray-600 text-sm py-8 text-center">No blocked queries yet.</p>
              : (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={data.top_blocked_patterns} layout="vertical">
                    <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }} />
                    <YAxis type="category" dataKey="pattern" tick={{ fill: "#9ca3af", fontSize: 12 }} width={60} />
                    <Tooltip
                      contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                      formatter={(v) => [v, "blocked"]}
                    />
                    <Bar dataKey="count" fill="#ef4444" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )
          }
        </div>
      </div>

      {/* Recent blocked */}
      <div className="card">
        <h2 className="text-sm font-semibold text-white mb-4">Recent Blocked Attempts</h2>
        <div className="space-y-2">
          {loading
            ? Array(5).fill(0).map((_, i) => (
                <div key={i} className="h-10 bg-gray-800 rounded animate-pulse" />
              ))
            : (data?.recent_blocked ?? []).length === 0
              ? <p className="text-gray-600 text-sm">No blocked attempts recorded.</p>
              : (data.recent_blocked).map((entry, i) => (
                  <div key={i} className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
                    <Badge label="BLOCKED" variant="BLOCKED" />
                    <div className="min-w-0 flex-1">
                      <p className="font-mono text-xs text-gray-300 truncate">{entry.query}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{entry.reason} · {entry.timestamp}</p>
                    </div>
                  </div>
                ))
          }
        </div>
      </div>
    </div>
  );
}
