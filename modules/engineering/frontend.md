---
name: frontend
description: >
  Frontend architecture: component patterns, state management, performance optimization, accessibility, responsive design, build optimization. Works with ANY frontend framework.
triggers: [UI, component, page, form, modal, CSS, styling, render, DOM, browser, SPA, SSR, hydration, responsive, layout, web app]
anti_triggers: [API endpoint, server logic, database query, Docker, CI/CD pipeline, iOS app, Android app]
last_verified: 2026-09-21
---

# Frontend Developer (pattern-based)

## Core Principles (technology-agnostic)

1. **Component-driven** — reusable, composable UI components
2. **Performance-first** — Core Web Vitals optimization
3. **Accessibility** — WCAG compliance, semantic HTML
4. **Responsive** — mobile-first, progressive enhancement
5. **Maintainable** — clear architecture, testable components

## Key Patterns

### Component Patterns
- Atomic design (atoms, molecules, organisms)
- Container/Presentational separation
- Render props, hooks, slots
- Compound components
- Higher-order components

### State Management
- Local state (component-level)
- Shared state (context, stores)
- Server state (caching, synchronization)
- URL state (query params, routing)
- Form state (validation, submission)

### Performance Patterns
- Code splitting (route, component)
- Lazy loading (images, components)
- Virtual scrolling (large lists)
- Memoization (pure components)
- Bundle optimization (tree shaking)

### Accessibility Patterns
- Semantic HTML elements
- ARIA labels and roles
- Keyboard navigation
- Screen reader support
- Focus management

### Responsive Patterns
- Mobile-first CSS
- Container queries
- Fluid typography
- Adaptive images
- Breakpoint system

## Anti-Patterns
- Bad: "Add more JavaScript" — violates performance-first
- Good: "Measure, then optimize hot paths" — satisfies performance-first

- Bad: "Skip accessibility testing" — violates accessibility
- Good: "Automated a11y checks in CI" — satisfies accessibility

## Output Contract
- Component architecture diagrams
- Performance budgets
- Accessibility audit results
- Responsive breakpoint system
- Build configuration