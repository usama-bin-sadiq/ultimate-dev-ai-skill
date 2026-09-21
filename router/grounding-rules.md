# Grounding Rules (compact)

## Grounding Sources (in order)
1. Code in repo
2. Loaded module principles
3. Sourced lookup per protocol

## Steps
1. **Identify claim type**:
   - Named library → official docs first
   - Broad concept → web search, authoritative sources
   - No tools → disclose as unverified

2. **Execute lookup**:
   - WebSearch/WebFetch if available
   - Named: official docs, npm/pypi/cargo, GitHub README
   - Frameworks: official guides

3. **Record note**: source URL + claim verified

4. **Persist**: recurring lookups → module tooling-notes

## Anti-Rules
- Never fabricate sources
- Never use blogs/forums over official docs
- Never present training-cutoff as current

## Compact Output
```
[ grounded: yes|no | source: <url> | claim: <what> ]
```