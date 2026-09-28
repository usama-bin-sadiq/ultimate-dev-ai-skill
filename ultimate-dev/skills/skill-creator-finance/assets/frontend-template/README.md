# frontend-template — React + Vite + Tailwind boilerplate

The project skeleton a `frontend-webapp-builder` skill copies instead of writing
from scratch. SKILL.md lists `assets/frontend-template/` as the "HTML/React
boilerplate" case for assets: a file the output is built from, never read into
context.

`assets/hello-world/` is the same idea at its smallest. Use that one when the
result is a single screen; use this one when the request mentions navigation,
several pages, or a layout that has to survive being extended.

> Reconstruction note: written from the SKILL.md description, not recovered from
> upstream. The dependency set, the file layout, and the class names are this
> template's own, chosen to be small and to have no build step that can fail for
> a reason unrelated to the app.

## Run it

```bash
npm install
npm run dev
```

## What is here

| path | what it is for |
|---|---|
| `src/main.tsx` | entry point; mounts the router inside the providers |
| `src/App.tsx` | the route table, and nothing else |
| `src/components/Layout.tsx` | the shell: header, nav, `<Outlet />` |
| `src/pages/Home.tsx` | the page the app opens on |
| `src/pages/About.tsx` | a second route, so routing is visibly working |
| `src/lib/cn.ts` | the one class-name joiner, so conditional classes compose |
| `src/index.css` | Tailwind entry plus the theme variables |
| `tailwind.config.js` | the Tailwind theme, in one place |
| `vite.config.ts`, `tsconfig*.json` | build configuration |

## Rules this template bakes in

- **Mobile-first.** Unprefixed utilities are the small screen; `sm:`, `md:`,
  `lg:` add to them. Do not write a `max-width` variant first.
- **Accessibility is not a layer on top.** Every interactive element is a real
  `button` or `a`; the focus ring is left in place; a page has exactly one `h1`.
- **No dependency without a use in this repo.** The four runtime dependencies
  are React, React DOM, the router, and the class joiner. That is deliberate —
  every extra package is one more thing to upgrade later.
- **Paths use the `@/` alias.** A bare relative specifier such as
  `components/Layout` breaks the moment a file moves up a directory;
  `@/components/Layout` does not.

## Replace these first

1. `index.html` — the `<title>` and the meta description.
2. `src/index.css` — the colour variables. Everything else reads from them.
3. `src/App.tsx` — the route table, once the real pages exist.
4. `src/components/Layout.tsx` — the nav, once the real sections exist.
