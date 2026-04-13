import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Puzzle, ScrollText, ShieldCheck, Database, Activity
} from "lucide-react";

const nav = [
  { to: "/dashboard", label: "Dashboard",  icon: LayoutDashboard },
  { to: "/skills",    label: "Skills",      icon: Puzzle },
  { to: "/logs",      label: "Query Logs",  icon: ScrollText },
  { to: "/security",  label: "Security",    icon: ShieldCheck },
  { to: "/database",  label: "Database",    icon: Database },
];

export default function Layout({ children }) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col shrink-0">
        <div className="px-5 py-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🦞</span>
            <div>
              <p className="font-bold text-white text-sm leading-tight">Skillhub</p>
              <p className="text-gray-500 text-xs">OpenClaw Manager</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? "bg-brand-600 text-white"
                    : "text-gray-400 hover:text-white hover:bg-gray-800"
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-gray-800">
          <p className="text-gray-600 text-xs">Olist E-Commerce Analytics</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto bg-gray-950">
        <div className="max-w-6xl mx-auto px-8 py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
