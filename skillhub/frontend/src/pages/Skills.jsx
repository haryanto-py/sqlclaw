import { useEffect, useState } from "react";
import { Puzzle, ExternalLink, Plus, Power } from "lucide-react";
import Badge   from "../components/Badge";
import { api } from "../api/client";

export default function Skills() {
  const [skills,  setSkills]  = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  
  const [showAddForm, setShowAddForm] = useState(false);
  const [newSkillName, setNewSkillName] = useState("");
  const [newSkillDesc, setNewSkillDesc] = useState("");

  const loadSkills = () => {
    setLoading(true);
    api.skills()
      .then((d) => setSkills(d.skills))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSkills();
  }, []);

  const handleToggle = async (skill) => {
    try {
      const isCurrentlyEnabled = skill.status === "active";
      await api.toggleSkill(skill.name, !isCurrentlyEnabled, skill.source);
      loadSkills();
    } catch (e) {
      setError("Failed to toggle skill: " + e.message);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newSkillName) return;
    try {
      await api.addSkill(newSkillName, newSkillDesc);
      setNewSkillName("");
      setNewSkillDesc("");
      setShowAddForm(false);
      loadSkills();
    } catch (e) {
      setError("Failed to add skill: " + e.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-white">Skills</h1>
          <p className="text-gray-400 text-sm mt-1">Registered OpenClaw skills and their status</p>
        </div>
        <button 
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-2 px-3 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors text-sm font-medium"
        >
          <Plus size={16} />
          Create Local Skill
        </button>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      {showAddForm && (
        <form onSubmit={handleAdd} className="card border-brand-800 bg-brand-900/10 flex flex-col gap-3">
          <h2 className="text-lg font-medium text-white">New Local Skill</h2>
          <div className="flex gap-4">
            <input 
              required
              type="text" 
              placeholder="Skill Name (e.g. hello_world)" 
              value={newSkillName}
              onChange={(e) => setNewSkillName(e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, ''))}
              className="bg-gray-900 border border-gray-700 rounded p-2 text-white flex-1 outline-none focus:border-brand-500"
            />
            <input 
              type="text" 
              placeholder="Description" 
              value={newSkillDesc}
              onChange={(e) => setNewSkillDesc(e.target.value)}
              className="bg-gray-900 border border-gray-700 rounded p-2 text-white flex-[2] outline-none focus:border-brand-500"
            />
            <button type="submit" className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded font-medium">Create</button>
          </div>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {loading
          ? Array(3).fill(0).map((_, i) => (
              <div key={i} className="card h-36 animate-pulse bg-gray-800" />
            ))
          : skills.map((skill) => (
              <div key={skill.name} className={`card flex flex-col gap-3 transition-opacity ${skill.status === 'active' ? '' : 'opacity-70'}`}>
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
                  <div className="flex items-center gap-3 shrink-0">
                    <div className="flex gap-1.5">
                      <Badge label={skill.type}   variant={skill.type} />
                      <Badge label={skill.status} variant={skill.status} />
                    </div>
                    <button 
                      onClick={() => handleToggle(skill)}
                      className={`p-1.5 rounded-full transition-colors ${skill.status === 'active' ? 'bg-green-500/20 text-green-400 hover:bg-red-500/20 hover:text-red-400' : 'bg-gray-800 text-gray-500 hover:bg-green-500/20 hover:text-green-400'}`}
                      title={skill.status === 'active' ? 'Disable Skill' : 'Enable Skill'}
                    >
                      <Power size={14} />
                    </button>
                  </div>
                </div>

                <p className="text-gray-400 text-sm leading-relaxed line-clamp-2">{skill.description}</p>

                {Object.keys(skill.config ?? {}).length > 0 && (
                  <div className="bg-gray-950 rounded-lg p-3 text-xs font-mono text-gray-400 overflow-x-auto">
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
    </div>
  );
}
