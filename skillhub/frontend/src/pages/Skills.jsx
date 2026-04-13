import { useEffect, useState } from "react";
import { Puzzle, ExternalLink } from "lucide-react";
import Badge   from "../components/Badge";
import { api } from "../api/client";

export default function Skills() {
  const [skills,  setSkills]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    api.skills()
      .then((d) => setSkills(d.skills))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Skills</h1>
        <p className="text-gray-400 text-sm mt-1">Registered OpenClaw skills and their status</p>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm">{error}</div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading
          ? Array(3).fill(0).map((_, i) => (
              <div key={i} className="card h-36 animate-pulse bg-gray-800" />
            ))
          : skills.map((skill) => (
              <div key={skill.name} className="card flex flex-col gap-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-gray-800 rounded-lg">
                      <Puzzle size={16} className="text-gray-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white text-sm">{skill.name}</p>
                      <p className="text-gray-500 text-xs font-mono">{skill.source}</p>
                    </div>
                  </div>
                  <div className="flex gap-1.5 shrink-0">
                    <Badge label={skill.type}   variant={skill.type} />
                    <Badge label={skill.status} variant={skill.status} />
                  </div>
                </div>

                <p className="text-gray-400 text-sm leading-relaxed">{skill.description}</p>

                {Object.keys(skill.config ?? {}).length > 0 && (
                  <div className="bg-gray-950 rounded-lg p-3 text-xs font-mono text-gray-400">
                    {Object.entries(skill.config).map(([k, v]) => (
                      <div key={k}>
                        <span className="text-gray-600">{k}: </span>
                        <span>{typeof v === "string" && v.startsWith("${") ? <span className="text-amber-400">{v}</span> : String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
        }

        {!loading && skills.length === 0 && (
          <div className="card col-span-2 text-center text-gray-500 py-12">
            No skills found. Check that <code className="text-gray-400">openclaw/openclaw.json</code> exists.
          </div>
        )}
      </div>

      <div className="card border-gray-800">
        <p className="text-xs text-gray-500">
          To install a new skill from ClawhHub, run:{" "}
          <code className="text-gray-300 bg-gray-800 px-1.5 py-0.5 rounded">
            npx clawhub@latest install &lt;skill-name&gt;
          </code>{" "}
          inside the <code className="text-gray-300 bg-gray-800 px-1.5 py-0.5 rounded">openclaw/</code> directory,
          then register it in <code className="text-gray-300 bg-gray-800 px-1.5 py-0.5 rounded">openclaw.json</code>.
        </p>
      </div>
    </div>
  );
}
