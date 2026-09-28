<!-- Moved verbatim from skillify/SKILL.md, the
     'step-4-capture-the-fixture' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 4 — Capture the fixture

```bash
$B goto "<TARGET_URL>"
$B html > /tmp/skillify-fixture-$$.html
```

The fixture filename inside the staged dir is
`fixtures/<host-with-dashes>-<YYYY-MM-DD>.html`, where the date is today.
E.g. `fixtures/lobste-rs-2026-04-27.html`.

Read the file you wrote, store its contents in a variable, and use it
when staging in step 7.
