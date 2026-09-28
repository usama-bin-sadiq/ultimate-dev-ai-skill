<!-- Moved verbatim from plan-tune/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Important Rules

- **Plain English everywhere.** Never require the user to know `profile set
  autonomy 0.4`. The skill interprets plain language; shortcuts exist for
  power users.
- **Confirm before mutating `declared`.** Agent-interpreted free-form edits are
  a trust boundary. Always show the intended change and wait for Y.
- **User-origin gate on tune: events.** `source: "plan-tune"` is only valid
  when the user invoked this skill directly. For inline `tune:` from other
  skills, the originating skill uses `source: "inline-user"` after verifying
  the prefix came from the user's chat message.
- **One-way doors override never-ask.** Even with a never-ask preference, the
  binary returns ASK_NORMALLY for destructive/architectural/security questions.
  Surface the safety note to the user whenever it fires.
- **No behavior adaptation in v1.** This skill INSPECTS and CONFIGURES. No
  skills currently read the profile to change defaults. That's v2 work, gated
  on the registry proving durable.
- **Completion status:**
  - DONE — did what the user asked (enable/inspect/set/update/disable)
  - DONE_WITH_CONCERNS — action taken but flagging something (e.g., "your
    profile shows a large gap — worth reviewing")
  - NEEDS_CONTEXT — couldn't disambiguate the user's intent
