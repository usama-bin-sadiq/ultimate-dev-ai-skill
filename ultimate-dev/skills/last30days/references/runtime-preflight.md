<!-- Moved verbatim from last30days/SKILL.md, the 'Runtime Preflight' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Runtime Preflight

Before running any `last30days.py` command in this skill, resolve a Python 3.12+ interpreter once and keep it in `LAST30DAYS_PYTHON`:

```bash
try_last30days_python() {
  candidate="$1"
  [ -n "$candidate" ] || return 1
  if [ -x "$candidate" ]; then
    :
  elif command -v "$candidate" >/dev/null 2>&1; then
    :
  else
    return 1
  fi
  "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || return 1
  LAST30DAYS_PYTHON="$candidate"
  return 0
}

windows_path_to_unix() {
  path="$1"
  [ -n "$path" ] || return 1
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$path"
  else
    printf '%s\n' "$path"
  fi
}

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  while IFS= read -r windows_python_root; do
    [ -n "$windows_python_root" ] && [ -d "$windows_python_root" ] || continue
    while IFS= read -r py; do
      try_last30days_python "$py" && break 2
    done <<EOF_PYTHON_CANDIDATES
$(find "$windows_python_root" -maxdepth 2 -type f -iname python.exe 2>/dev/null | sort -r)
EOF_PYTHON_CANDIDATES
  done <<EOF_WINDOWS_PYTHON_ROOTS
$([ -n "${LOCALAPPDATA:-}" ] && printf '%s\n' "$(windows_path_to_unix "$LOCALAPPDATA")/Programs/Python")
$([ -n "${ProgramFiles:-}" ] && windows_path_to_unix "$ProgramFiles")
$([ -n "${PROGRAMFILES:-}" ] && windows_path_to_unix "$PROGRAMFILES")
$(program_files_x86="$(printenv 'ProgramFiles(x86)' 2>/dev/null || true)"; [ -n "$program_files_x86" ] && windows_path_to_unix "$program_files_x86")
EOF_WINDOWS_PYTHON_ROOTS
fi

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  for py in python3.14 python3.13 python3.12 python3 python; do
    try_last30days_python "$py" && break
  done
fi

# uv fallback: on hosts without a system 3.12 but with `uv` on PATH (most agent
# sandboxes: Cowork, Codex, etc.), provision a managed 3.12 automatically instead
# of hard-failing. No-op when uv is absent — those hosts still hit the error below.
if [ -z "${LAST30DAYS_PYTHON:-}" ] && command -v uv >/dev/null 2>&1; then
  uv_py="$(uv python find '>=3.12' 2>/dev/null)"
  if [ -z "$uv_py" ] || [ ! -x "$uv_py" ]; then
    echo "NOTE: no Python 3.12+ found; installing a managed CPython 3.12 via uv (~28MB, one-time)." >&2
    if UV_HTTP_TIMEOUT=30 uv python install 3.12 >/dev/null 2>&1; then
      uv_py="$(uv python find '>=3.12' 2>/dev/null)"
    else
      echo "WARN: 'uv python install 3.12' failed (network, disk space, or proxy?); falling through to the version-gate error below." >&2
    fi
  fi
  try_last30days_python "$uv_py"
fi

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  echo "ERROR: last30days v3 requires Python 3.12+. Install Python 3.12+ or set LAST30DAYS_PYTHON to a supported interpreter." >&2
  exit 1
fi

"${LAST30DAYS_PYTHON}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || {
  echo "ERROR: LAST30DAYS_PYTHON must point to Python 3.12+." >&2
  exit 1
}

LAST30DAYS_MEMORY_DIR="${LAST30DAYS_MEMORY_DIR:-$HOME/Documents/Last30Days}"
```

**PYTHON VERSION GATE — when the Runtime Preflight Bash block above exits with a Python version error:**

If the preflight script (including the uv fallback above) emits `ERROR: last30days v3 requires Python 3.12+` (or `LAST30DAYS_PYTHON must point to Python 3.12+`) and exits, you MUST:

1. Display this message to the user:
   > "The last30days engine needs Python 3.12+. Your system has an older version. Install it with one command:
   > - **Mac:** `brew install python@3.12`
   > - **Windows:** `winget install Python.Python.3.12`
   > - **Linux:** `sudo apt install python3.12` (or `pyenv install 3.12`)
   >
   > Then re-run `/last30days <your topic>` and the setup wizard will configure everything automatically."
2. **Stop.** Do not attempt research. Do not fall back to WebSearch-only synthesis.

WebSearch-only synthesis is not equivalent to running the engine — it misses Reddit community data, X/Twitter timelines, YouTube transcripts, TikTok, and Polymarket. Presenting it without disclosure misleads the user about what was actually searched. This is the same category of failure as a WebSearch-only run with no engine footer.

**Native-search signal (web coverage).** If you (the hosting model) have your own web-search tool available, export `LAST30DAYS_NATIVE_SEARCH=1` in the same shell before invoking the engine:

```bash
export LAST30DAYS_NATIVE_SEARCH=1   # ONLY when you have a native web-search tool
```

Your host search is better than the engine's keyless web fallback, so this tells the engine to skip that fallback and leave general web to you (you already run web-search supplements in Step 2). If you have NO web-search tool in the agent session, do **not** set this: the engine's keyless web floor supplies general-web coverage automatically. The rule is capability-based, not host-name-based — set it only when you genuinely have a better search, never to suppress the floor on a host that has nothing else.
