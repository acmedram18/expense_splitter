import { NavLink, Outlet } from "react-router-dom";
import { useTheme } from "../theme.js";
import ThemeToggle from "./ThemeToggle.jsx";

const links = [
  { to: "/", label: "Resumen", end: true },
  { to: "/expenses", label: "Gastos" },
  { to: "/members", label: "Miembros" },
  { to: "/settle", label: "Liquidar" },
];

export default function Layout() {
  const [theme, toggle] = useTheme();

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">{"//"}</span>
          <span className="brand-name">EntreNos</span>
        </div>
        <nav className="nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
        <ThemeToggle theme={theme} onToggle={toggle} />
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}