#!/usr/bin/env bash
# Repair the reference damage left by flattening the imported collections.
#
# Every step is guarded: a rewrite only happens when its target is known to
# exist in this tree. Steps that would need a human decision are absent on
# purpose -- run tools/check-links.py afterwards to see what is left.
#
# Idempotent: re-running it changes nothing.
set -euo pipefail
cd "$(dirname "$0")/ultimate-dev"   # -> ultimate-dev/ (the skill tree)

SK=skills
say() { printf '\n=== %s\n' "$1"; }

# ---------------------------------------------------------------- S0 vercel
# vercel-deploy held the script; deploy-to-vercel's own text already pointed at
# resources/deploy.sh, which did not exist. Also repoint a second reference to a
# script name that never existed (deploy-codex.sh).
if [ -d "$SK/vercel-deploy" ]; then
  say "S0  vercel: land the script where the docs already point"
  mkdir -p "$SK/deploy-to-vercel/resources" "$SK/deploy-to-vercel/assets"
  mv "$SK/vercel-deploy/scripts/deploy.sh" "$SK/deploy-to-vercel/resources/deploy.sh"
  chmod +x "$SK/deploy-to-vercel/resources/deploy.sh"
  cp "$SK/vercel-deploy/assets/vercel.png" "$SK/vercel-deploy/assets/vercel-small.svg" \
     "$SK/deploy-to-vercel/assets/" 2>/dev/null || true
  rm -rf "$SK/vercel-deploy"
  echo "    removed skills/vercel-deploy/"
fi
sed -i '' 's|resources/deploy-codex\.sh|resources/deploy.sh|g' "$SK/deploy-to-vercel/SKILL.md" 2>/dev/null || true

# ------------------------------------------------------------- S1 artifacts
# web-artifacts-builder is a byte-identical superset (same scripts, plus the
# vendored shadcn archive), so the loser needs no porting.
if [ -d "$SK/artifacts-builder" ]; then
  say "S1  artifacts: drop the byte-identical subset"
  rm -rf "$SK/artifacts-builder"
  echo "    removed skills/artifacts-builder/"
fi

# ------------------------------------------------- S2 template-family merges
if [ -d "$SK/email-sequence" ]; then
  say "S2  template-family merges (X <- 'Use this one, X')"
  python3 tools/merge-dupes.py
fi

# --------------------------------------------------- S3 phantom collection v1
# marketing-skill/skills/<path>  ->  skills/<path>
say "S3  marketing-skill/skills/ -> skills/"
python3 - <<'PY'
import pathlib
n = 0
for p in list(pathlib.Path('skills').glob('*/**/*.md')) + list(pathlib.Path('agents').glob('*.md')):
    s = p.read_text(errors='ignore')
    if 'marketing-skill/skills/' not in s: continue
    c = s.count('marketing-skill/skills/')
    s = s.replace('../../marketing-skill/skills/', 'skills/').replace('marketing-skill/skills/', 'skills/')
    p.write_text(s); n += c
print(f'    {n} refs')
PY

# --------------------------------------------------- S4 phantom collection v2
# marketing-skill/<name> -> skills/<name>, only when skills/<name> exists
say "S4  marketing-skill/<name> -> skills/<name>"
python3 - <<'PY'
import re, pathlib
pat = re.compile(r'(?<![\w/-])marketing-skill/([A-Za-z0-9_][A-Za-z0-9_.-]*)(?![\w.-])')
n = 0
for p in list(pathlib.Path('skills').glob('*/**/*.md')) + list(pathlib.Path('agents').glob('*.md')):
    s = p.read_text(errors='ignore')
    if 'marketing-skill/' not in s: continue
    def repl(m):
        global n
        name = m.group(1)
        if pathlib.Path('skills', name).is_dir():
            n += 1; return f'skills/{name}'
        return m.group(0)
    new = pat.sub(repl, s)
    if new != s: p.write_text(new)
print(f'    {n} refs')
PY

# ------------------------------------------------ S5 whole-bundle prose fixups
# "marketing-skill" also names the *bundle*. This repo is flat, so reword.
say "S5  whole-bundle references (the repo is flat)"
python3 - <<'PY'
import pathlib
E = [
 ("skills/plugin-audit/SKILL.md",
  "4. Detect domain from path: `engineering/`, `product-team/`, `marketing-skill/`, etc.",
  "4. Detect domain from the owning collection — here every skill lives under `skills/<name>/`; in a multi-plugin repo the top-level directory is the domain."),
 ("skills/plugin-audit/SKILL.md",
  "| `marketing-skill/` | cs-content-creator | Content quality, SEO optimization, brand voice |",
  "| `skills/` (marketing) | cs-content-creator | Content quality, SEO optimization, brand voice |"),
 ("skills/rfp-responder/SKILL.md",
  "- Marketing collateral / category content → `marketing-skill/*`",
  "- Marketing collateral / category content → any marketing skill under `skills/`"),
 ("skills/internal-comms/SKILL.md",
  "- Customer-facing launch comms / press release / blog post → `marketing-skill/*`",
  "- Customer-facing launch comms / press release / blog post → any marketing skill under `skills/`"),
 ("skills/marketing-ops/SKILL.md",
  "### Cross-Domain (route outside marketing-skill/)",
  "### Cross-Domain (route outside the marketing skills)"),
 ("skills/sales-engineer/SKILL.md",
  "- **Marketing Skills** - Leverage competitive intelligence and messaging frameworks from `marketing-skill/`",
  "- **Marketing Skills** - Leverage competitive intelligence and messaging frameworks from the marketing skills under `skills/`"),
 ("skills/research-ops-skills/SKILL.md",
  "- **`marketing-skill`** — that's **campaign analytics and demand-gen**. market-research is **upstream methodology**.",
  "- **The marketing skills** (`campaign-analytics`, `marketing-demand-acquisition`) — that's **campaign analytics and demand-gen**. market-research is **upstream methodology**."),
 ("skills/marketing-skills/SKILL.md",
  "All paths are relative to `marketing-skill/`.",
  "All paths below are relative to the `skills/` directory."),
 ("skills/cs-content-creator/SKILL.md",
  "- **Marketing domain guide:** [../../marketing-skill/<agent-instructions>](../../marketing-skill/<agent-instructions>)\n- **Agent development guide:** [../<agent-instructions>](../<agent-instructions>)",
  "- **Marketing domain guide:** [skills/marketing-skills/SKILL.md](../marketing-skills/SKILL.md)\n- **Agent development guide:** [skills/agent-development/SKILL.md](../agent-development/SKILL.md)"),
 ("skills/rfp-responder/SKILL.md",
  "**`marketing-skill/*`**", "**the marketing skills** (`skills/*`)"),
 ("skills/internal-comms/SKILL.md",
  "**`marketing-skill/*`**", "**the marketing skills** (`skills/*`)"),
]
n = 0
for f, old, new in E:
    p = pathlib.Path(f)
    if not p.is_file(): continue
    s = p.read_text()
    if old not in s:
        print(f"    SKIP (already applied or moved): {f}"); continue
    p.write_text(s.replace(old, new, 1)); n += 1
print(f'    {n} rewordings')
PY

# --------------------------------------------------- S6 doubled skills prefix
say "S6  doubled skills/skills/ prefix"
python3 - <<'PY'
import re, pathlib
n = 0
for p in list(pathlib.Path('skills').glob('*/**/*.md')) + list(pathlib.Path('agents').glob('*.md')):
    s = p.read_text(errors='ignore')
    if 'skills/skills/' not in s: continue
    def repl(m):
        global n
        if pathlib.Path('skills', m.group(1)).is_dir():
            n += 1; return f'skills/{m.group(1)}'
        return m.group(0)
    new = re.sub(r'skills/skills/([A-Za-z0-9_.-]+)', repl, s)
    if new != s: p.write_text(new)
print(f'    {n} refs')
PY

# ------------------------------------- S7 upstream collection prefix (tool)
say "S7  <collection>/skills/<name> -> skills/<name>"
python3 tools/normalize-collection-refs.py

# --------------------------------------------------- S8 cs-*.md sibling links
say "S8  cs-*.md -> ../cs-*/SKILL.md"
python3 - <<'PY'
import re, pathlib
pat = re.compile(r"\]\((cs-[a-z0-9-]+)\.md\)")
n = 0
for d in sorted(pathlib.Path('skills').glob('cs-*')):
    f = d / 'SKILL.md'
    if not f.is_file(): continue
    s = f.read_text()
    def repl(m):
        global n
        name = m.group(1)
        if pathlib.Path('skills', name, 'SKILL.md').is_file():
            n += 1; return f'](../{name}/SKILL.md)'
        return m.group(0)
    new = pat.sub(repl, s)
    if new != s: f.write_text(new)
print(f'    {n} links')
PY

# ------------------------------------------ S9 the one link my merge deleted
say "S9  ../email-sequence -> ../emails"
sed -i '' 's|\.\./email-sequence|../emails|g' "$SK/cs-demand-gen-specialist/SKILL.md" 2>/dev/null || true

# ------------------------------------------------- S10 unambiguous link repair
say "S10 uniquely-resolvable link repoints"
python3 tools/repair-links.py

say "done -- now run tools/check-links.py to see what remains"
