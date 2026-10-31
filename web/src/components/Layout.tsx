import { useEffect } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { useAppState } from "../lib/AppState";
import { Icon, type IconName } from "./Icon";
import { PulsieAvatar } from "./Pulsie";

const NAV: { to: string; label: string; icon: IconName; end?: boolean }[] = [
  { to: "/", label: "Home", icon: "home", end: true },
  { to: "/check/about-you", label: "New check", icon: "clipboard" },
  { to: "/history", label: "History", icon: "history" },
  { to: "/learn", label: "Learn", icon: "book" },
];

function isActiveCheck(pathname: string, to: string) {
  return to.startsWith("/check") && (pathname.startsWith("/check") || pathname.startsWith("/result"));
}

export function Layout() {
  const { pathname } = useLocation();
  const { schemaState } = useAppState();

  // Block body on purpose: newer browsers return a Promise from scrollTo, and React
  // would treat any returned value as a cleanup function and crash.
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [pathname]);

  const links = NAV.map((item) => (
    <NavLink
      key={item.to} to={item.to} end={item.end}
      className={({ isActive }) =>
        `nav__link ${isActive || isActiveCheck(pathname, item.to) ? "is-active" : ""}`}
    >
      <Icon name={item.icon} size={19} />
      <span>{item.label}</span>
    </NavLink>
  ));

  return (
    <div className="app">
      <a className="skip-link" href="#main">Skip to content</a>
      <header className="topbar">
        <div className="topbar__inner">
          <Link to="/" className="brand" aria-label="HyperPredict home">
            <PulsieAvatar size={40} />
            <span className="brand__name">Hyper<span>Predict</span></span>
          </Link>
          <nav className="nav nav--top" aria-label="Main">{links}</nav>
        </div>
      </header>

      <main id="main" className="main" key={pathname}>
        <Outlet />
      </main>

      <footer className="footer">
        <div className="footer__inner">
          <p className="footer__status">
            {schemaState.status === "ready" && (
              <><span className="status-dot status-dot--ok" /> Model connected: {schemaState.schema.model_name} (v{schemaState.schema.schema_version})</>
            )}
            {schemaState.status === "loading" && <><span className="status-dot" /> Connecting to the model…</>}
            {schemaState.status === "error" && <><span className="status-dot status-dot--error" /> Model server not reachable</>}
          </p>
          <p>HyperPredict is a university machine-learning project for education only. It does not diagnose hypertension.</p>
        </div>
      </footer>

      <nav className="nav nav--bottom" aria-label="Main (mobile)">{links}</nav>
    </div>
  );
}
