import { useEffect, useState } from "react";
import { Play, Database as DbIcon } from "lucide-react";
import { api } from "../api/client";

export default function Database() {
  const [tables,  setTables]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  const [sql,        setSql]        = useState("");
  const [queryResult,setQueryResult]= useState(null);
  const [queryError, setQueryError] = useState(null);
  const [running,    setRunning]    = useState(false);

  useEffect(() => {
    api.tables()
      .then((d) => setTables(d.tables))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  function loadSample(query) {
    setSql(query);
    setQueryResult(null);
    setQueryError(null);
  }

  async function runQuery(e) {
    e.preventDefault();
    if (!sql.trim()) return;
    setRunning(true);
    setQueryError(null);
    setQueryResult(null);
    try {
      const result = await api.runQuery(sql);
      setQueryResult(result);
    } catch (err) {
      setQueryError(err.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Database</h1>
        <p className="text-gray-400 text-sm mt-1">Table statistics and interactive query runner</p>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm">{error}</div>
      )}

      {/* Tables list */}
      <div className="card p-0 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/50">
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Table</th>
              <th className="text-right px-4 py-3 text-gray-400 font-medium">Rows</th>
              <th className="text-right px-4 py-3 text-gray-400 font-medium">Size</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium">Sample Query</th>
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array(9).fill(0).map((_, i) => (
                  <tr key={i} className="border-b border-gray-800">
                    {Array(4).fill(0).map((_, j) => (
                      <td key={j} className="px-4 py-3">
                        <div className="h-4 bg-gray-800 rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              : tables.map((t) => (
                  <tr key={t.name} className="table-row">
                    <td className="px-4 py-3 font-mono text-sm text-gray-200">{t.name}</td>
                    <td className="px-4 py-3 text-right text-gray-300">{t.rows.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right text-gray-500 text-xs">{t.size}</td>
                    <td className="px-4 py-3">
                      {t.sample_query && (
                        <button
                          onClick={() => loadSample(t.sample_query)}
                          className="text-xs text-brand-400 hover:text-brand-300 font-mono truncate max-w-xs block"
                          title={t.sample_query}
                        >
                          {t.sample_query.substring(0, 60)}…
                        </button>
                      )}
                    </td>
                  </tr>
                ))
            }
          </tbody>
        </table>
      </div>

      {/* Query runner */}
      <div className="card space-y-4">
        <div className="flex items-center gap-2">
          <DbIcon size={16} className="text-gray-400" />
          <h2 className="text-sm font-semibold text-white">Query Runner</h2>
          <span className="text-xs text-gray-500 ml-1">(SELECT only — max 200 rows)</span>
        </div>

        <form onSubmit={runQuery} className="space-y-3">
          <textarea
            className="input w-full h-32 font-mono text-xs resize-none"
            placeholder="SELECT order_status, COUNT(*) FROM orders GROUP BY order_status;"
            value={sql}
            onChange={(e) => setSql(e.target.value)}
          />
          <button type="submit" disabled={running} className="btn-primary flex items-center gap-2">
            <Play size={14} />
            {running ? "Running…" : "Run Query"}
          </button>
        </form>

        {queryError && (
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-3 text-red-400 text-xs font-mono">
            {queryError}
          </div>
        )}

        {queryResult && (
          <div className="overflow-x-auto">
            <p className="text-gray-500 text-xs mb-2">{queryResult.count} rows returned</p>
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-800">
                  {queryResult.columns.map((col) => (
                    <th key={col} className="text-left px-3 py-2 text-gray-400 font-medium whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {queryResult.rows.map((row, i) => (
                  <tr key={i} className="table-row">
                    {queryResult.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-gray-300 font-mono whitespace-nowrap">
                        {row[col] === null ? <span className="text-gray-600">NULL</span> : String(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
