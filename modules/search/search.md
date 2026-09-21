---
name: search
description: >
  Search engines, full-text search, search relevance, indexing strategies, autocomplete, faceted search. Works with ANY search technology.
triggers: [search, full-text search, search relevance, autocomplete, faceted search, indexing, search engine]
anti_triggers: [database queries, API design, frontend UI, caching]
last_verified: 2026-09-21
---

# Search Module

## Core Principles (technology-agnostic)

1. **Relevance** — results must match user intent
2. **Performance** — sub-100ms response times
3. **Scalability** — handle growing data and traffic
4. **Typo tolerance** — fuzzy matching for user errors
5. **Analytics** — track search behavior for improvement

## Key Patterns

### Search Architecture
- Dedicated search engine (not database LIKE)
- Index optimization
- Query optimization
- Result ranking

### Indexing Strategies
- Document structure
- Field mapping
- Analyzer configuration
- Index optimization

### Relevance Tuning
- TF-IDF vs BM25
- Boosting rules
- Synonyms
- Personalization

### Features
- Autocomplete
- Faceted search
- Filter queries
- Highlighting

## Anti-Patterns
- Bad: "Use database LIKE queries for search" — violates performance
- Good: "Use dedicated search engine with proper indexing" — satisfies performance

- Bad: "Ignore search analytics" — violates analytics principle
- Good: "Track searches, clicks, conversions" — satisfies analytics

## Output Contract
- Search architecture diagrams
- Index configurations (generic)
- Relevance tuning rules
- Performance benchmarks
- Analytics dashboards