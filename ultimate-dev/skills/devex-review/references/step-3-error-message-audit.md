<!-- Moved verbatim from devex-review/SKILL.md, the
     'step-3-error-message-audit' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 3: Error Message Audit

Trigger common error scenarios:
- Aside: Open a 404 URL, submit an invalid form (on a non-LOCAL target that is a mutating
  action — one AskUserQuestion per run first, per the browser rules), open a protected URL
- CLI: Run with missing args, invalid flags, bad input

Screenshot each error. Score against the Elm/Rust/Stripe three-tier model.

Score 0-10. Load "## Pass 3" from dx-hall-of-fame.md for calibration.
