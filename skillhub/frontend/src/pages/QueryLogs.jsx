import { useEffect, useState, useCallback } from "react";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import Badge   from "../components/Badge";
import { api } from "../api/client";

export default function QueryLogs() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [page,    setPage]    = useState(1);
  const [status,  setStatus]  = useState("all");
  const [search,  setSearch]  = useState("");
  const [inputVal,setInputVal]= useState("");

  const limit = 50;

  const load = useCallback(() => {
    setLoading(true);
    api.queryLogs({ page, limit, status, search })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [page, status, search]);

  useEffect(() => { load(); }, [load]);

  const totalPages = data ? Math.ceil(data.total / limit) : 1;

  function handleSearch(e) {
    e.preventDefault();
    setSearch(inputVal);
    setPage(1);
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Query Logs</h1>
        <p className="text-gray-400 text-sm mt-1">All SQL queries processed by the validator</p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-500" />
            <input
              className="input pl-8 w-64"
              placeholder="Search queries..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary">Search</button>
        </form>

        <div className="flex gap-1">
          {["all", "ALLOWED", "BLOCKED"].map((s) => (
            <button
              key={s}
              onClick={() => { setStatus(s); setPage(1); }}
              className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                status === s
                  ? "bg-brand-600 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {s === "all" ? "All" : s}
            </button>
          ))}
        </div>

        {data && (
          <p className="text-gray-500 text-sm ml-auto">
            {data.total.toLocaleString()} results
          </p>
        )}
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm">{error}</div>
      )}

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/50">
              <th className="text-left px-4 py-3 text-gray-400 font-medium w-44">Timestamp</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium w-24">Status</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Query</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium w-48">Reason</th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array(10).fill(0).map((_, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    {Array(4).fill(0).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-800 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              : (data?.entries ?? []).map((entry, i) => (
                  <tr key={i} className="table-row">
                    <td className="px-4 py-3 text-gray-500 text-xs font-mono whitespace-nowrap">
                      {entry.timestamp}
                    </td>
                    <td className="px-4 py-3">
                      <Badge label={entry.status} variant={entry.status} />
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-300 max-w-md">
                      <p className="truncate" title={entry.query}>{entry.query}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {entry.reason || "—"}
                    </td>
                  </tr>
                ))
            }
            {!loading && (data?.entries ?? []).length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-12 text-center text-gray-600">
                  No queries found.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="btn-ghost disabled:opacity-30"
          >
            <ChevronLeft size={16} />
          </button>
          <span className="text-gray-400 text-sm">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="btn-ghost disabled:opacity-30"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
