
import { NavLink, Outlet } from "react-router-dom";
import "./Layout.css";

const navigation = [
  { label: "Assessment", path: "/" },
  { label: "Person-Job Fit Results", path: "/results" },
  { label: "Model Insights", path: "/insights" },
  { label: "About", path: "/about" },
];

export default function Layout() {
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="brand">swytch</div>

        <p className="nav-heading">YOUR JOURNEY</p>

        <nav aria-label="Main navigation">
          {navigation.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `nav-link ${isActive ? "active" : ""}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <strong>Research prototype</strong>
          <p>Exploring job satisfaction and person-job fit.</p>
        </div>
      </aside>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
