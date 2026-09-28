import { useState } from "react";

/**
 * The whole app. Replace this file; do not grow it into a component tree that
 * every other file has to be read in order to understand.
 */
export default function App() {
  const [count, setCount] = useState(0);

  return (
    <main
      style={{
        fontFamily: "system-ui, sans-serif",
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        gap: "1rem",
      }}
    >
      <h1>Hello, world.</h1>
      <p>
        You clicked {count} {count === 1 ? "time" : "times"}.
      </p>
      <button type="button" onClick={() => setCount((value) => value + 1)}>
        Click me
      </button>
    </main>
  );
}
