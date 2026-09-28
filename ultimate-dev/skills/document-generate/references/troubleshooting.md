<!-- Moved verbatim from document-generate/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Troubleshooting

[Common failure modes and their fixes. Pull from tests and error handling code.]
```

**Rules for how-to docs:**
- Title starts with "How to" — no exceptions. This is the reader's entry point.
- Every step must be actionable. No "consider whether..." — instead "Run X" or "Add Y to Z".
- Include verification. The reader should never wonder "did it work?"
- Troubleshooting section is mandatory if the task can fail.

---

## Step 6: Write Tutorials

Tutorials are learning-oriented. They take a newcomer from zero to a working example.
These are the hardest to write well and the most valuable.

**Tutorial doc template:**

```markdown
# [Tutorial title — describes what you'll build/learn]

[Opening paragraph: what you'll build, why it's useful, and what you'll understand
by the end. Keep it concrete — "You'll build a working X that does Y" not
"This tutorial covers X".]

## What you'll need

[Prerequisites: tools, versions, prior knowledge. Link to installation guides.]

## Step 1: [Set up the foundation]

[Start from a clean state. Show every command. Explain what each does on first
encounter — but briefly, not a lecture.]

```bash
[exact command]
```

[Brief explanation of what just happened.]
