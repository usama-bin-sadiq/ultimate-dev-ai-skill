<!-- Moved verbatim from design-shotgun/SKILL.md, the 'Step 5: Feedback Confirmation' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 5: Feedback Confirmation

After receiving feedback (via HTTP POST or AskUserQuestion fallback), output a clear
summary confirming what was understood:

"Here's what I understood from your feedback:

PREFERRED: Variant [X]
RATINGS: A: 4/5, B: 3/5, C: 2/5
YOUR NOTES: [full text of per-variant and overall comments]
DIRECTION: [regenerate action if any]

Is this right?"

Use AskUserQuestion to confirm before saving.
