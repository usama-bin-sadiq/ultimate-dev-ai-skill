---
name: accessibility
description: >
  Web accessibility: WCAG compliance, semantic HTML, ARIA, keyboard navigation, screen reader support, color contrast, focus management. Technology-agnostic.
triggers: [accessibility, a11y, WCAG, ARIA, screen reader, keyboard navigation, semantic HTML, focus management, color contrast]
anti_triggers: [database schema, API design, Git operations, CI/CD pipeline]
last_verified: 2026-09-21
---

# Accessibility Module (pattern-based)

## Core Principles (technology-agnostic)

1. **Perceivable** — content must be presentable to all users
2. **Operable** — UI components must be operable by all users
3. **Understandable** — information and UI must be understandable
4. **Robust** — content must be interpreted by assistive technologies
5. **Inclusive by default** — accessibility is not an afterthought

## Key Patterns

### Semantic HTML Patterns
- Use native HTML elements (button, nav, main, article)
- Headings hierarchy (h1 → h2 → h3)
- Lists for list content
- Tables for tabular data
- Forms with labels and fieldsets

### ARIA Patterns
- Roles for custom components
- States and properties
- Live regions for dynamic content
- Landmark roles
- Relationship attributes (aria-describedby)

### Keyboard Patterns
- Visible focus indicators
- Logical tab order
- Keyboard shortcuts
- Focus trapping (modals)
- Skip navigation links

### Screen Reader Patterns
- Alt text for images
- Labels for form inputs
- Hidden text for context
- Announce dynamic changes
- Table headers and captions

### Color & Visual Patterns
- Color contrast (4.5:1 minimum)
- Don't rely on color alone
- Responsive text sizing
- Dark mode support
- Reduced motion support

### Testing Patterns
- Automated testing (axe, Lighthouse)
- Manual testing (keyboard only)
- Screen reader testing
- User testing with disabilities
- Regression testing

## Anti-Patterns
- Bad: "Add ARIA to everything" — violates semantic HTML
- Good: "Use native elements first, ARIA only when needed" — satisfies semantic HTML

- Bad: "No focus indicators" — violates keyboard patterns
- Good: "Visible, high-contrast focus rings" — satisfies keyboard patterns

## Output Contract
- Accessibility audit results
- WCAG compliance report
- Remediation recommendations
- Test scripts
- Training documentation