import { Routes, Route, Navigate } from "react-router-dom";
import Layout    from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Skills    from "./pages/Skills";
import QueryLogs from "./pages/QueryLogs";
import Security  from "./pages/Security";
import Database  from "./pages/Database";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/"          element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/skills"    element={<Skills />} />
        <Route path="/logs"      element={<QueryLogs />} />
        <Route path="/security"  element={<Security />} />
        <Route path="/database"  element={<Database />} />
      </Routes>
    </Layout>
  );
}
