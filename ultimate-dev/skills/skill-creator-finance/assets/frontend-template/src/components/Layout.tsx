import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/cn";

const navigation = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
];

/**
 * The app shell. Every route renders inside it, so this is the only place that
 * decides what surrounds the content.
 */
export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-10 focus:rounded focus:bg-brand focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-white"
      >
        Skip to content
      </a>

      <header className="border-b border-line">
        <nav
          aria-label="Main"
          className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-3"
        >
          <span className="text-sm font-semibold tracking-tight">Frontend Template</span>
          <ul className="flex items-center gap-1 text-sm">
            {navigation.map((item) => (
              <li key={item.to}>
                <NavLink
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    cn(
                      "rounded px-2 py-1 transition-colors",
                      "hover:bg-surface-raised",
                      isActive && "font-semibold text-brand",
                    )
                  }
                >
                  {item.label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>
      </header>

      <main id="main" className="mx-auto w-full max-w-3xl flex-1 px-4 py-10">
        <Outlet />
      </main>

      <footer className="border-t border-line">
        <p className="mx-auto max-w-3xl px-4 py-6 text-sm text-ink-muted">
          Replace this footer, or delete it.
        </p>
      </footer>
    </div>
  );
}
