import { useEffect, useState } from "react";
import { Activity, Server, RefreshCw } from "lucide-react";
import { api } from "../api/client";

export default function Gateway() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkStatus = () => {
    setLoading(true);
    api.gatewayStatus()
      .then((d) => setStatus(d))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 10000); // Check every 10 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-white">Gateway Status</h1>
          <p className="text-gray-400 text-sm mt-1">Monitor the local OpenClaw gateway container process</p>
        </div>
        <button 
          onClick={checkStatus}
          disabled={loading}
          className="p-2 text-gray-400 hover:text-white bg-gray-900 border border-gray-800 rounded-lg transition-colors"
        >
          <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm">
          Failed to fetch gateway status: {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-xl ${status?.status === 'running' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
              <Activity size={24} />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Status</p>
              <p className="text-xl font-bold text-white capitalize">
                {loading && !status ? "Checking..." : status?.status || "Unknown"}
              </p>
            </div>
          </div>
        </div>

        <div className="card flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-500/20 text-blue-400 rounded-xl">
              <Server size={24} />
            </div>
            <div>
              <p className="text-gray-400 text-sm">Address</p>
              <p className="text-xl font-bold text-white font-mono">
                {status ? `${status.host}:${status.port}` : "---"}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="card border-gray-800">
        <h3 className="text-lg font-medium text-white mb-2">Process Management</h3>
        <p className="text-gray-400 text-sm mb-4">
          Because OpenClaw is currently running as a terminal command on your machine, it must be restarted manually from your command prompt.
        </p>
        <div className="bg-gray-950 p-4 rounded-lg border border-gray-800">
          <code className="text-brand-400 block mb-2"># To restart the gateway:</code>
          <code className="text-gray-300 block">1. Open the terminal where it is running</code>
          <code className="text-gray-300 block">2. Press <span className="bg-gray-800 px-1 rounded">Ctrl + C</span> to stop</code>
          <code className="text-gray-300 block">3. Run <span className="bg-gray-800 px-1 rounded">openclaw gateway run</span> again</code>
        </div>
      </div>
    </div>
  );
}
