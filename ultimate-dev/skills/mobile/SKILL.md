---
name: mobile-skill
description: >
  Meta-cognitive skill for mobile development. Teaches HOW to think about
  mobile constraints — connectivity, device capabilities, platform policies —
  regardless of specific framework or platform.
triggers: [mobile, app, offline, push, notification, device, touch, gesture, portable]
provides: mobile_ability
---

# Mobile Skill — Build for Any Device

## Purpose

An **ability**. Mobile is about constraints: small screens, unreliable networks,
limited battery, platform policies. This skill teaches you how to think about
mobile for ANY platform.

## The Ability

```
Given any mobile problem, you can:
1. Identify the constraints (screen, network, battery, permissions)
2. Design for offline-first (network is a bonus, not a requirement)
3. Handle platform differences gracefully
4. Optimize for the device (not the cloud)
5. Respect platform policies and user privacy
```

## How to Build for ANY Mobile Platform

### Step 1: Understand the Constraints

```
Mobile is NOT desktop. Every decision must account for:

SCREEN:      Small, varied sizes, notch/cutout, orientation changes
NETWORK:     Unreliable, slow, metered, offline
BATTERY:     Limited, background restrictions
MEMORY:      Limited, OS may kill background apps
INPUT:       Touch, gestures, no hover, keyboard covers screen
PERMISSIONS: User must grant, can be revoked
PLATFORM:    iOS vs Android vs Web — different rules, different UX
```

### Step 2: Design Offline-First

```
RULE: The app should work without network. Network is a bonus.

Pattern:
1. Cache data locally (SQLite, IndexedDB, file system)
2. Queue writes when offline
3. Sync when network returns
4. Handle conflicts (last-write-wins or merge)
5. Show sync status to user
```

### Step 3: Handle Platform Differences

```
For ANY cross-platform work:
1. Identify what's platform-specific vs shared
2. Shared: Business logic, data models, API calls
3. Platform-specific: UI, navigation, native features
4. Use abstractions for platform APIs
5. Test on BOTH platforms (don't assume)
```

### Step 4: Optimize for Device

```
Performance rules:
- Lazy load everything (images, screens, data)
- Compress images aggressively
- Minimize network requests
- Use background threads for heavy work
- Cache aggressively (network, computed data)
- Monitor memory usage
```

### Step 5: Respect the User

```
Privacy and UX:
- Request permissions ONLY when needed (not at startup)
- Explain WHY you need each permission
- Don't track without consent
- Don't drain battery in background
- Don't use excessive storage
- Provide clear opt-out for data collection
```

## Mobile Anti-Patterns

- DO NOT skip offline support (users lose connectivity)
- DO NOT ignore platform-specific UI guidelines
- DO NOT request all permissions at once
- DO NOT skip crash reporting
- DO NOT ignore app size impact on download rates
