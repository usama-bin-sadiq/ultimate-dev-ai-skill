<!-- Moved verbatim from learn/SKILL.md, the
     'manual-add' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Manual add

The user wants to manually add a learning. Use AskUserQuestion to gather:
1. Type (pattern / pitfall / preference / architecture / tool)
2. A short key (2-5 words, kebab-case)
3. The insight (one sentence)
4. Confidence (1-10)
5. Related files (optional)

Then log it:

```bash
~/<agent-config-dir>/gstack/bin/gstack-learnings-log '{"skill":"learn","type":"TYPE","key":"KEY","insight":"INSIGHT","confidence":N,"source":"user-stated","files":["FILE1"]}'
```
