<!-- Moved verbatim from ios-qa/SKILL.md, the
     'prerequisites' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Prerequisites

- macOS (the daemon uses `devicectl` from Xcode).
- iPhone connected via USB, paired and trusted.
- Xcode + Swift toolchain installed (`swift --version` reports >= 5.9).
- App source available on disk, with at least one `@Observable` class.
- For remote-control mode: Tailscale installed and the user logged in.
