<!-- Moved verbatim from ios-qa/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Phase 2: Bootstrap the device bridge

1. Generate the canonical local bridge package, typed accessors, and installed
   version marker with one deterministic command:
   ```bash
   ~/.claude/skills/gstack/bin/gstack-ios-qa-regen \
     --app-source "<source-dir>" \
     --bridge-dir "<source-dir>/DebugBridge"
   ```
   The regenerator also removes the explicit obsolete flat-file set created by
   older ios-sync versions, preventing a stale second harness from remaining
   in the app target.
2. Add the generated `DebugBridge` local SPM dependency to the app's
   `Package.swift`. The package
   ships three Debug-config-only library products:
   - `DebugBridgeCore` (Swift, cross-platform) — StateServer + bridge protocols.
   - `DebugBridgeTouch` (Objective-C, iOS-only) — KIF-derived in-process touch
     synthesis with iOS 18+ `_UIHitTestContext` SwiftUI hit-testing.
   - `DebugBridgeUI` (Swift, iOS-only) — Screenshot / Elements / Mutation
     bridge implementations.
   The app target depends on `DebugBridgeUI` with `.when(configuration: .debug)`
   (transitively pulls in Core + Touch). Release builds refuse to link these
   targets.
3. Wire the bridges from the `@main` App init, gated on `#if DEBUG`:
   ```swift
   #if DEBUG
   import DebugBridgeCore
   #if canImport(UIKit)
   import DebugBridgeUI
   // Install resolvers before StateServer opens its listener.
   DebugBridgeUIWiring.installAll()
   #endif
   // Replace AppState/AppStateAccessor with the type discovered in Phase 1.
   DebugBridgeManager.shared.start(
       appState: appState,
       register: AppStateAccessor.register
   )
   #endif
   ```
4. Build + deploy to the device with `xcodebuild -scheme <SchemeName>
   -destination 'platform=iOS,id=<UDID>' build install`.
5. Launch via `devicectl device process launch --device <UDID> --console <bundle-id>`.
   Capture the boot token printed to `os_log` on first run.
6. Spawn the Mac-side daemon (on-demand) — `gstack-ios-qa-daemon`. Daemon
   acquires an exclusive flock on `~/.gstack/ios-qa-daemon.pid`. If another
   daemon is alive, the second invocation discovers its port and connects.
7. Daemon immediately calls `POST /auth/rotate` on the iOS StateServer with a
   fresh in-memory-only token. The boot token becomes useless ~5s later.
   Anything scraping `os_log` past this point sees a dead credential.
   If a fresh daemon finds the app running after another daemon consumed that
   one-use token, it verifies the bundle owner, relaunches the target once,
   waits for the new token, verifies ownership again, and then rotates.
