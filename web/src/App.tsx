import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { AppStateProvider } from "./lib/AppState";
import { History } from "./pages/History";
import { Learn } from "./pages/Learn";
import { NotFound } from "./pages/NotFound";
import { PersonalInfo } from "./pages/PersonalInfo";
import { PulseInfo } from "./pages/PulseInfo";
import { Result } from "./pages/Result";
import { Welcome } from "./pages/Welcome";

export function App() {
  return (
    <AppStateProvider>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Welcome />} />
            <Route path="check" element={<Navigate to="/check/about-you" replace />} />
            <Route path="check/about-you" element={<PersonalInfo />} />
            <Route path="check/pulse" element={<PulseInfo />} />
            <Route path="result/:id" element={<Result />} />
            <Route path="history" element={<History />} />
            <Route path="learn" element={<Learn />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppStateProvider>
  );
}
