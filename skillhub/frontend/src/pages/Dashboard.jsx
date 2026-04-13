import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Database, ShieldAlert, Activity, CheckCircle, XCircle } from "lucide-react";
import StatCard  from "../components/StatCard";
import Badge     from "../components/Badge";
import LiveLogs  from "../components/LiveLogs";
import { api }  from "../api/client";

export default function Dashboard() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState(null);

  useEffect(() => {
    api.dashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const tableData = data?.tables?.slice(0, 9) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 text-sm mt-1">OpenClaw agent overview</p>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm">{error}</div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Database"
          value={data?.db_connected ? "Online" : "Offline"}
          sub={data?.db_connected ? `${(data.total_rows ?? 0).toLocaleString()} total rows` : data?.db_error}
          icon={data?.db_connected ? CheckCircle : XCircle}
          color={data?.db_connected ? "green" : "red"}
          loading={loading}
        />
        <StatCard
          label="Total Rows"
          value={data ? (data.total_rows ?? 0).toLocaleString() : null}
          sub="across 9 tables"
          icon={Database}
          color="blue"
          loading={loading}
        />
        <StatCard
          label="Queries Today"
          value={data?.queries_today ?? 0}
          sub={`${data?.blocked_today ?? 0} blocked`}
          icon={Activity}
          color="purple"
          loading={loading}
        />
        <StatCard
          label="Total Blocked"
          value={data?.total_blocked ?? 0}
          sub={`of ${(data?.total_queries ?? 0).toLocaleString()} total queries`}
          icon={ShieldAlert}
          color="red"
          loading={loading}
        />
      </div>

      {/* Table row counts chart */}
      <div className="card">
        <h2 className="text-sm font-semibold text-white mb-4">Table Row Counts</h2>
        {loading
          ? <div className="h-48 bg-gray-800 rounded animate-pulse" />
          : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={tableData} layout="vertical" margin={{ left: 40, right: 20 }}>
                <XAxis type="number" tick={{ fill: "#6b7280", fontSize: 11 }}
                  tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v} />
                <YAxis type="category" dataKey="name" tick={{ fill: "#9ca3af", fontSize: 11 }} width={160} />
                <Tooltip
                  contentStyle={{ background: "#111827", border: "1px solid #374151", borderRadius: 8 }}
                  labelStyle={{ color: "#f9fafb" }}
                  formatter={(v) => [v.toLocaleString(), "rows"]}
                />
                <Bar dataKey="rows" radius={[0, 4, 4, 0]}>
                  {tableData.map((_, i) => (
                    <Cell key={i} fill={`hsl(${200 + i * 15}, 70%, 55%)`} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )
        }
      </div>

      {/* Recent queries + live logs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card">
          <h2 className="text-sm font-semibold text-white mb-3">Recent Queries</h2>
          <div className="space-y-2">
            {loading
              ? Array(5).fill(0).map((_, i) => (
                  <div key={i} className="h-10 bg-gray-800 rounded animate-pulse" />
                ))
              : (data?.recent_queries ?? []).map((q, i) => (
                  <div key={i} className="flex items-start gap-2 py-1.5 border-b border-gray-800 last:border-0">
                    <Badge label={q.status} variant={q.status} />
                    <p className="text-gray-400 text-xs font-mono truncate flex-1">{q.query}</p>
                  </div>
                ))
            }
            {!loading && (data?.recent_queries ?? []).length === 0 && (
              <p className="text-gray-600 text-sm">No queries logged yet.</p>
            )}
          </div>
        </div>

        <LiveLogs />
      </div>
    </div>
  );
}
