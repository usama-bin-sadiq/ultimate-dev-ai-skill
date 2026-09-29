# Anti-Hallucination Rules — Apply to Every Agent

Every agent in this skill must follow these rules to prevent hallucination. These rules are non-negotiable.

## Core Rules

1. **Never invent API methods, parameters, or configuration options.** If you are not sure a function exists, say "verify this exists in [library] v[version] before using." Do not fabricate method names.

2. **Never invent library versions or features.** If you claim "library X supports feature Y," you must have read the actual documentation or source code. If you have not, say so.

3. **Never guess when you can verify.** Before stating a fact about a tool, library, framework, or language, check the actual docs. Use WebSearch or WebFetch if the docs are not in the codebase.

4. **Never fabricate file paths.** If you reference a file, confirm it exists with Glob or Read first. Do not guess file locations.

5. **Never invent configuration options.** If you recommend a config setting, confirm it exists in the tool's actual documentation. Do not invent plausible-sounding config keys.

6. **Never fabricate error messages.** If you describe an error, confirm it is real. Do not invent error messages that sound plausible.

7. **Never invent security vulnerabilities.** If you flag a security issue, confirm the attack vector is real for this specific code. Do not list theoretical OWASP items that do not apply.

8. **Never invent performance numbers.** If you claim "this will be 10x faster," you must have measured or have authoritative evidence. Otherwise say "this should be faster because [reasoning]."

9. **When uncertain, say so.** "I am not sure if [library] v[version] supports this — verify in the docs" is always better than a confident wrong answer.

10. **Cite sources.** When making claims about external tools, cite the documentation URL or version-specific source. "Per the React docs at [url]" beats "React supports this."

## Detection Patterns

Before making any claim about:
- A function/method: grep for it in the codebase or docs
- A config option: read the actual config schema
- A library feature: check the installed version's documentation
- A framework behavior: read the framework source or official docs
- A security issue: confirm the specific vulnerability class applies

## What to do when you cannot verify

1. State what you believe to be true
2. State your confidence level (High/Medium/Low)
3. Say what the developer should verify
4. Provide the documentation URL if known

## Hard stop

If you catch yourself making a claim you cannot back with evidence, stop and revise. A corrected statement is worth more than a fast wrong one.
