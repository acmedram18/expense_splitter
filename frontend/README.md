# A Medias — frontend

React + Vite single-page app for the Expense Splitter (see root `README.md`
and `_docs/specs.md`).

- Backend calls are centralized in `src/api.js`. It currently runs against a
  mock persisted to `localStorage`; swap it for `fetch()` when the backend
  exists (the pages don't change).

## Commands

```bash
npm install
npm run dev      # dev server → http://localhost:5173
npm run build    # production build to dist/
npm run lint     # oxlint
```