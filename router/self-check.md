# Self-Check (compact)

## Process Checks
- [ ] Classification block present
- [ ] Tier matches classification
- [ ] Only justified modules loaded
- [ ] Token budget respected
- [ ] Domain checklists applied
- [ ] Tier + modules declared

## Content Checks
- [ ] No fabricated APIs/versions/paths
- [ ] No unverified claims as fact
- [ ] No silent scope creep
- [ ] High-risk actions gated
- [ ] Sub-agent context minimized
- [ ] Completion checklist run

## Output Format
```
[ tier: atomic|moderate|complex | modules: none|<list> | retries: 0|<n> ]
```

## Correction Protocol
1. Identify failed check
2. Fix issue
3. Re-run check
4. Don't return until all pass

## Model-Adaptive
| Model | Checks |
|-------|--------|
| tiny | process checks only |
| small | process + first 3 content |
| large | all checks |
| huge | all + additional audit |