import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./auth";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Medications from "./pages/Medications";
import Register from "./pages/Register";
import Scan from "./pages/Scan";
import Scans from "./pages/Scans";
import Profile from "./pages/Profile";
import Today from "./pages/Today";
import CalendarPage from "./pages/Calendar";

export default function App() {
  const { loggedIn } = useAuth();

  if (!loggedIn) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    );
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/today" element={<Today />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/medications" element={<Medications />} />
        <Route path="/scan" element={<Scan />} />
        <Route path="/scans" element={<Scans />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  );
}
