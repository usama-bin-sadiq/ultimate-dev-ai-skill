<!-- Moved verbatim from ios-qa/SKILL.md, the
     'phase-1-read-source-plan-codegen' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Phase 1: Read source, plan codegen

1. Before changing the app or replacing an installed build, verify that the
   bridge is compatible with the project:
   - The generator currently supports file-scope `@Observable` classes only;
     `ObservableObject`, `@StateObject`, and other observation models do not
     produce accessors.
   - The documented dependency wiring assumes a SwiftPM app manifest. For an
     `.xcodeproj` or `.xcworkspace`, do not invent package or target wiring.
   If either requirement is unmet, stop the bridge bootstrap without modifying
   the app. Preserve any installed production or TestFlight build. Prefer an
   existing real-device XCUITest harness; when a separate QA build is needed,
   use an isolated bundle identifier and non-production entitlements so it can
   coexist with the production app. Report fixture-driven state, provider UI,
   and actual external-provider success as distinct evidence tiers.
2. Walk the app source (passed as `--source <dir>`) and identify all `@Observable`
   classes. Note any property immediately preceded by the generator marker
   comment `// @Snapshotable` — those are the snapshot-eligible fields. The
   marker is a comment so it composes with the `@Observable` macro. Each
   marked field must belong to a file-scope observable class and be a writable
   instance `var` with an explicit type and an internal or public setter.
   Snapshot types are JSON-native scalars (`String`, `Bool`, integer widths,
   `Float`, `Double`, `CGFloat`), arrays, String-keyed dictionaries, and their
   Optional compositions. Keys must be unique across observable classes.
   Codegen stops with a source diagnostic instead of emitting a broken or
   lossy harness when any of these constraints is violated.
3. Show the user the accessor list and ask whether to install the DebugBridge
   SPM dependency into their `Package.swift` (one AskUserQuestion).
