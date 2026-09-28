export default function Home() {
  return (
    <section>
      <h1 className="text-3xl font-semibold tracking-tight">Home</h1>
      <p className="mt-3 max-w-prose text-ink-muted">
        Replace this page. Keep one <code className="font-mono">h1</code> per route, keep
        paragraphs under about 70 characters wide, and let the layout do the spacing.
      </p>
      <button
        type="button"
        className="mt-6 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white transition-colors hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
      >
        A real action
      </button>
    </section>
  );
}
