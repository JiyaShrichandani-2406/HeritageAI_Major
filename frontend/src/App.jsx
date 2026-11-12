import { Routes, Route, Navigate } from "react-router-dom";

import Home from "./pages/Home.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Monuments from "./pages/Monuments.jsx";
import MonumentDetail from "./pages/MonumentDetail.jsx";
import Chat from "./pages/Chat.jsx";
import PlanTrip from "./pages/PlanTrip.jsx";
import Itinerary from "./pages/Itinerary.jsx";
import Nearby from "./pages/Nearby.jsx";
import NotFound from "./pages/NotFound.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/monuments" element={<Monuments />} />
      <Route path="/monuments/:id" element={<MonumentDetail />} />
      <Route path="/chat" element={<Chat />} />
      <Route path="/plan" element={<PlanTrip />} />
      <Route path="/plan/results" element={<Itinerary />} />
      <Route path="/nearby" element={<Nearby />} />
      <Route path="/home" element={<Navigate to="/" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
