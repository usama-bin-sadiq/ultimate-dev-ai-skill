<!-- Moved verbatim from devex-review/SKILL.md, the
     'scope-declaration' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Scope Declaration

Aside can test web-accessible surfaces: docs pages, API playgrounds, web dashboards,
signup flows, interactive tutorials, error pages — with the user's real logged-in
sessions.

Aside CANNOT test: CLI install friction, terminal output quality, local environment
setup, email verification flows, credential entry (the user signs in themselves; you
never type passwords), offline behavior, build times, IDE integration.

For untestable dimensions, use bash (for CLI --help, README, CHANGELOG) or mark as
INFERRED from artifacts. Never guess. State your evidence source for every score.
