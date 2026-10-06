`openapi.yaml` has three defects. Produce a corrected copy at
`out/openapi.fixed.yaml` and a summary at `out/changes.txt`.

The three defects:

1. The server URL points at `https://api.example.com/latest` — an unpinned,
   moving version. Pin it to the concrete `v1`.
2. The `getUser` operation has no `404` response, so a missing user is
   undocumented. Add an explicit `404` response.
3. All errors are folded into a single `default` response. Replace it with
   explicit `400` and `500` responses.

`out/changes.txt` must contain the three words `pin`, `404` and `replace` (one
per line, any order, any surrounding prose). Keep the rest of the document
intact.
