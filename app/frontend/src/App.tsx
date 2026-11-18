
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./components/Layout";
import Assessment from "./pages/Assessment";
import Results from "./pages/Results";
import Insights from "./pages/Insights";
import About from "./pages/About";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Assessment />} />
          <Route path="/results" element={<Results />} />
          <Route path="/insights" element={<Insights />} />
          <Route path="/about" element={<About />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
