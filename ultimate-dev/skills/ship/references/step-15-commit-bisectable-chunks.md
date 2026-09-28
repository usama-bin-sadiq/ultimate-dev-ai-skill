<!-- Moved verbatim from ship/SKILL.md, the
     'step-15-commit-bisectable-chunks' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 15: Commit (bisectable chunks)

Create small, logical commits for `git bisect`. If all changes are already committed, continue to Step 16; never create an empty commit.

1. Group by coherent change. Keep each model/service/controller with its tests;
   keep controller views together. Migrations may stand alone or accompany their
   model; config/routes may accompany the feature they enable. A diff under
   50 lines across fewer than 4 files may use one commit.
2. Order dependencies first: infrastructure → models/services → controllers/views.
   Each commit must work independently, without broken imports or missing code.
   VERSION + CHANGELOG + TODOS.md belong in the final commit.
3. Use `<type>: <summary>` (feat/fix/chore/refactor/docs) and a brief body.
   Only the final VERSION/CHANGELOG commit gets the version tag and co-author trailer:

```bash
git commit -m "$(cat <<'EOF'
chore: bump version and changelog (vX.Y.Z.W)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---
