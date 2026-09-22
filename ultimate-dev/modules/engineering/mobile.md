---
name: mobile
description: >
  Mobile app architecture, cross-platform patterns, offline sync, push notifications, app store optimization, performance optimization. Works with ANY mobile framework.
triggers: [iOS, Android, mobile, cross-platform, push notification, offline sync, app store, mobile app, responsive mobile]
anti_triggers: [web browser, desktop app, API endpoint, database schema]
last_verified: 2026-09-21
---

# Mobile Specialist (pattern-based)

## Core Principles (technology-agnostic)

1. **Offline-first** — design for connectivity loss
2. **Performance** — 60fps, fast startup, low memory
3. **Platform conventions** — follow iOS/Android guidelines
4. **Security** — secure storage, biometrics, encryption
5. **Testing** — unit, integration, device testing

## Key Patterns

### Architecture Patterns
- MVVM (Model-View-ViewModel)
- Clean Architecture
- Redux/MobX state management
- Repository pattern
- Dependency injection

### Offline Patterns
- Local database sync
- Conflict resolution
- Queue-based sync
- Optimistic updates
- Background sync

### Performance Patterns
- Lazy loading
- Image optimization
- Memory management
- Battery optimization
- Network optimization

### Platform Patterns
- Navigation patterns (tab, stack, drawer)
- Permission handling
- Deep linking
- Push notification handling
- Biometric authentication

### Testing Patterns
- Unit tests (business logic)
- Integration tests (API calls)
- UI tests (user flows)
- Device farm testing
- Performance profiling

## Anti-Patterns
- Bad: "Ignore platform guidelines" — violates platform conventions
- Good: "Follow Material Design/HIG" — satisfies platform conventions

- Bad: "Assume always online" — violates offline-first
- Good: "Design for connectivity loss" — satisfies offline-first

## Output Contract
- Architecture diagrams
- Platform-specific implementations
- Offline sync strategies
- Performance profiles
- Test coverage reports