import { useEffect, useState } from "react";
import { Users as UsersIcon, Plus, Trash2 } from "lucide-react";
import { api } from "../api/client";

export default function Users() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [newUser, setNewUser] = useState("");

  const loadUsers = () => {
    setLoading(true);
    api.users()
      .then((d) => setUsers(d.allowFrom || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newUser) return;
    const userId = parseInt(newUser.trim());
    if (isNaN(userId)) {
      setError("User ID must be a number");
      return;
    }
    
    if (users.includes(userId)) return;
    
    const newAllowFrom = [...users, userId];
    try {
      await api.updateUsers(newAllowFrom);
      setNewUser("");
      loadUsers();
    } catch (e) {
      setError("Failed to add user: " + e.message);
    }
  };

  const handleRemove = async (userId) => {
    const newAllowFrom = users.filter((u) => u !== userId);
    try {
      await api.updateUsers(newAllowFrom);
      loadUsers();
    } catch (e) {
      setError("Failed to remove user: " + e.message);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-white">Users</h1>
          <p className="text-gray-400 text-sm mt-1">Manage authorized Telegram users</p>
        </div>
      </div>

      {error && (
        <div className="card border-red-800 bg-red-900/20 text-red-400 text-sm flex justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-gray-400 hover:text-white">✕</button>
        </div>
      )}

      <div className="card max-w-2xl">
        <form onSubmit={handleAdd} className="flex gap-3 mb-6">
          <input 
            type="text" 
            placeholder="Telegram User ID (e.g. 1204658206)" 
            value={newUser}
            onChange={(e) => setNewUser(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded p-2 text-white flex-1 outline-none focus:border-brand-500"
          />
          <button type="submit" className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded font-medium">
            <Plus size={16} />
            Add User
          </button>
        </form>

        <div className="space-y-3">
          {loading ? (
            <div className="animate-pulse flex gap-2 h-12 bg-gray-800 rounded"></div>
          ) : users.length === 0 ? (
            <div className="text-center text-gray-500 py-8">No users are currently whitelisted. The bot may be open to everyone or disabled!</div>
          ) : (
            users.map((userId) => (
              <div key={userId} className="flex justify-between items-center p-3 bg-gray-900 border border-gray-800 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gray-800 rounded-full">
                    <UsersIcon size={16} className="text-gray-400" />
                  </div>
                  <span className="font-mono text-gray-300">{userId}</span>
                </div>
                <button 
                  onClick={() => handleRemove(userId)}
                  className="p-2 text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-full transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
