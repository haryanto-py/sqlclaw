import { Routes, Route, Navigate } from "react-router-dom";
import Layout    from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Skills    from "./pages/Skills";
import QueryLogs from "./pages/QueryLogs";
import Security  from "./pages/Security";
import Database  from "./pages/Database";
import Users     from "./pages/Users";
import Gateway   from "./pages/Gateway";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/"          element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/skills"    element={<Skills />} />
        <Route path="/users"     element={<Users />} />
        <Route path="/gateway"   element={<Gateway />} />
        <Route path="/logs"      element={<QueryLogs />} />
        <Route path="/security"  element={<Security />} />
        <Route path="/database"  element={<Database />} />
      </Routes>
    </Layout>
  );
}
