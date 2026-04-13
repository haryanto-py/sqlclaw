import { useEffect, useRef, useState } from "react";

export default function LiveLogs() {
  const [lines, setLines] = useState([]);
  const [connected, setConnected] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/live`);

    ws.onopen  = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (e) => {
      setLines((prev) => [...prev.slice(-499), e.data]);
    };

    return () => ws.close();
  }, []);

  // Auto-scroll to bottom on new lines
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white">Live Agent Log</h3>
        <span className={`flex items-center gap-1.5 text-xs ${connected ? "text-green-400" : "text-gray-500"}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-green-400 animate-pulse" : "bg-gray-600"}`} />
          {connected ? "Connected" : "Disconnected"}
        </span>
      </div>

      <div className="bg-gray-950 rounded-lg p-3 h-64 overflow-y-auto font-mono text-xs space-y-0.5">
        {lines.length === 0
          ? <p className="text-gray-600">Waiting for log output...</p>
          : lines.map((line, i) => (
              <p key={i} className="text-gray-400 break-all leading-relaxed">{line}</p>
            ))
        }
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
