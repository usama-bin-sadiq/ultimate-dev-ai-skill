`config.yaml` uses shell-style interpolation in its values, in two forms:

- `${NAME:-default}` — use `default` when `NAME` is unset
- `${NAME:?message}` — fail when `NAME` is unset

Rewrite the file to `out/config.yaml` keeping the same YAML structure, keys and
ordering, but replacing **every** interpolation with the bare form `${NAME}`.
Strip the `:-default` and `:?message` parts; keep the `${` and `}`.

Then write how many substitutions you made to `out/count.txt` as a bare
integer.
