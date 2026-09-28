import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section>
      <h1 className="text-3xl font-semibold tracking-tight">Not found</h1>
      <p className="mt-3 text-ink-muted">
        That route does not exist.{" "}
        <Link to="/" className="text-brand underline underline-offset-2">
          Go home
        </Link>
        .
      </p>
    </section>
  );
}
