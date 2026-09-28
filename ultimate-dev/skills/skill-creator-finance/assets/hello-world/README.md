# hello-world — React app boilerplate

The smallest React + TypeScript + Vite project that runs. Copy this directory,
change what is in `src/App.tsx`, and you have an app.

SKILL.md cites this as the stored boilerplate for a `frontend-webapp-builder`
skill: *"Writing a frontend webapp requires the same boilerplate HTML/React each
time."* Nothing here is clever. It is the part that gets rewritten every time and
should not have to be.

> Reconstruction note: written from the SKILL.md description, not recovered from
> upstream. The layout is this file's own; the file list is the minimum a Vite
> React TypeScript app needs.

## Run it

```bash
npm install
npm run dev
```

## What is here

| path | what it is for |
|---|---|
| `index.html` | the single page the app mounts into |
| `src/main.tsx` | the entry point: finds the root node, mounts `<App />` |
| `src/App.tsx` | the whole app, in one file, to be replaced |
| `src/index.css` | the reset and body styles |
| `vite.config.ts` | dev server and build configuration |
| `tsconfig.json` | TypeScript settings |
| `package.json` | dependencies and scripts |

`src/App.tsx` is deliberately one file. Splitting it before there is anything to
split produces a directory of one-line components that all have to be read
together anyway.
