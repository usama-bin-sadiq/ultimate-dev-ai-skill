<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the
     'step-2-collect-all-figma-file-links' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 2 — Collect All Figma File Links

Now that you know the extraction approach, ask for all Figma file URLs in one go — before starting any extraction. This avoids interrupting the workflow later.

Ask the user:

> "Please share the URL(s) for all Figma files that contain your design tokens. If your tokens are spread across multiple files or pages (e.g. colours in one file, typography in another), share all of them now and tell me what each file contains."

Wait for all URLs before proceeding. Extract the file key from each URL — the alphanumeric string between `/design/` and the next `/`. Note what token types each file/page contains.

> **Community files note:** If any URL is from a Figma community file the user has not duplicated to their account, warn them now: the extraction tools cannot access community files directly. Ask them to duplicate the file to their drafts in Figma first (open the file → **Duplicate to your drafts**), then share the new URL.

---
