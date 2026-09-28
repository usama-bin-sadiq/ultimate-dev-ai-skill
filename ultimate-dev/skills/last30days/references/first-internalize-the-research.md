<!-- Moved verbatim from last30days/SKILL.md, the
     'first-internalize-the-research' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## FIRST: Internalize the Research

**CRITICAL: Ground your synthesis in the ACTUAL research content, not your pre-existing knowledge.**

Read the research output carefully. Pay attention to:
- **Exact product/tool names** mentioned (e.g., if research mentions "ClawdBot" or "@clawdbot", that's a DIFFERENT product than "Claude Code" - don't conflate them)
- **Specific quotes and insights** from the sources - use THESE, not generic knowledge
- **What the sources actually say**, not what you assume the topic is about

**ANTI-PATTERN TO AVOID**: If user asks about "clawdbot skills" and research returns ClawdBot content (self-hosted AI agent), do NOT synthesize this as "Claude Code skills" just because both involve "skills". Read what the research actually says.

**FUN CONTENT (see LAW 9): the EVIDENCE block's `## Top Community Comments` section (present when 2+ relevance-qualified comments exist and the GENERAL nothing-solid floor did not fire) and any `## Best Takes` section are the voice of the people - weave at least 2 of the funniest/cleverest VERBATIM quotes into your synthesis.** A 1,338-upvote comment that says "Where's the limewire link" tells you more about the cultural moment than a news article. Quote the actual text and attribute the commenter; when you inline-link the comment on a hidden-link host (Claude Code; Grok Bot / Cursor agent chat) copy its URL verbatim from the block (never reconstructed), and on a visible-URL host (Codex, Gemini CLI, raw CLI) keep the attribution plain and leave the URL to the saved raw file. Don't put fun content in a separate section - mix it into the narrative where it fits naturally. This is what makes the report feel alive rather than like a news summary. Do NOT wait for a `## Best Takes` section - it is often empty; `## Top Community Comments` is the always-on source when qualifying comments remain.

**ELI5 MODE: If REGISTER is `eli5` (including the legacy `ELI5_MODE=true` fallback), apply these writing guidelines to your ENTIRE synthesis. Otherwise skip this block completely and write normally.**

ELI5 Mode: Explain it to me like I'm 5 years old.

- Assume I know nothing about this topic. Zero context.
- No jargon without a quick explanation in parentheses
- Short sentences. One idea per sentence.
- Start with the single most important thing that happened, in one line
- Use analogies when they help ("think of it like...")
- Keep the same structure: narrative, key patterns, stats, invitation
- Still quote real people and cite sources - don't lose the grounding
- Don't be condescending. Simple is not stupid. ELI5 means accessible, not childish.

Example - normal: "Arizona's identity is paint scoring (50%+ shooting, 9th nationally) and rebounding behind Big 12 Player of the Year Jaden Bradley."
Example - ELI5: "Arizona wins by being physical - they score most of their points close to the basket and they're one of the best shooting teams in the country."

Same data. Same sources. Just clearer.

### If QUERY_TYPE = RECOMMENDATIONS — Signal-weighted picks, not mention counts

**The failure mode for RECOMMENDATIONS queries is "counting when you should have judged."** Mention count rewards whatever is already popular, which is rarely what is actually recommended. Rank by signal quality instead.

**Signal weights (highest to lowest):**
1. **Practitioner testimony** (weight 5) - first-person "I use X and here's why" with specific reasoning, version numbers, or workflow details
2. **Expert defection / authority move** (weight 4) - a domain insider publicly switching, endorsing, or picking (e.g., Flask creator switching from Python to Go)
3. **Measurable claim** (weight 4) - specific number, benchmark, production adoption proof (e.g., "43.7% latency win", "LinkedIn and Uber running it in prod")
4. **Reasoned comparison** (weight 3) - side-by-side analysis with tradeoffs explicitly named
5. **Pattern across independent sources** (weight 2) - multiple unaffiliated voices converging on the same pick
6. **Descriptive mention** (weight 1) - "X is a Python framework" — existence, not recommendation
7. **Promotional / bootcamp / course-caption** (weight 0) - "comment CODE for my course" — skip entirely, do not count

**Before ranking, separate "what EXISTS" from "what is RECOMMENDED":**
- EXISTS = descriptive mentions, promotional content, training-data inertia, bootcamp curriculum, "learn X first" posts with no stakes attached
- RECOMMENDED = reasoned picks from voices with stakes in the outcome (practitioners, experts, case studies, people who switched)
- Only RECOMMENDED items drive the top of the ranking. Existing-but-not-recommended items go in "Also mentioned" at the bottom with a one-line note on why they are mentions not picks.

**Lead with the 30-day DELTA, not the status-quo baseline.** What is the interesting movement? Who is switching? What is the contrarian signal? A status-quo leader with no movement is a footer item, not the headline. "Python has 15 mentions" is not a delta; "Flask creator switched to Go this month" is.

**Output shape:**

```
🏆 Top recommendations (ranked by signal quality, not mention count):

**[Pick 1]** - [one-line why it is the top recommendation based on the strongest signal in the research]
- Evidence: [specific practitioner testimony, benchmark number, or expert pick - quote the actual signal]
- Best for: [specific use case]
- Voices: [real @handles, publications, or r/subreddits with stakes in the outcome]

**[Pick 2]** - [same shape]

**[Pick 3]** - [same shape]

Also mentioned (exists, not recommended): [comma-separated list with one-line note on WHY each is a mention rather than a pick - e.g., "Python (status-quo default across bootcamp content; @javitm: 'agents have a strong bias for Python despite it probably not being the best')"]
```

**Anti-patterns to avoid:**
- Leading with the most-mentioned option because it appears most frequently ("Python has 15 mentions so it is #1"). That is counting, not judging.
- Treating every mention equally. A Flask-creator switching to Go (expert defection, weight 4) outranks 10 bootcamp captions saying "learn Python first" (promotional, weight 0). The bootcamp captions do not belong in the ranking at all.
- Collapsing "best for what?" into one leaderboard. RECOMMENDATIONS queries usually split into 2-4 sub-questions (best for production scale, best for agents to generate reliably, best for learning, best for benchmarks). Separate them if the research supports it.
- Ignoring anti-signal quotes. If the corpus contains a quote like "@javitm: agents have a strong bias for Python despite it probably not being the best — they prioritize the strongest signal in training data over the right choice," that is telling you mention-count is a biased metric for this topic. Read it; surface it; do not ignore it.
- Stress-test your top pick before emitting. Ask: "Would the research actually defend this claim to a skeptical expert?" If the answer is no, re-rank.

**Named failure mode (2026-04-18):** On `best programming language for AI agents`, Opus 4.7 led with `🏆 Most mentioned: Python (15+x mentions)` and put Go at #3 with 7x mentions. Model self-debug: "I counted when I should have judged. @javitm's quote should have changed the ranking because it called Python mentions a bias signal, not evidence of fit. I read that quote and then ranked by mention count anyway. The Flask-creator switching to Go was the real headline; I buried it." Do not repeat this failure.

**BAD RECOMMENDATIONS synthesis (counting):**
> "🏆 Most mentioned: Python (15 mentions), TypeScript (10x), Go (7x), Rust (5x)."

**GOOD RECOMMENDATIONS synthesis (judging):**
> "🏆 Top recommendations (ranked by signal quality, not mention count):
>
> **Go** - Flask creator Miguel Grinberg publicly switched this month for a specific technical reason
> - Evidence: @miguelgrinberg blog post "Why I am moving Python projects to Go for AI agents" — cites reliability and concurrency model; 1.2K upvotes on r/programming
> - Best for: production agent infrastructure
> - Voices: @miguelgrinberg, r/programming, r/golang
>
> **Rust** - Hardest numbers in the corpus
> - Evidence: production benchmark showing 43.7% latency reduction and 16x throughput growth in agent workloads; LangChain Rust port announcement
> - Best for: performance-critical agent runtimes
> - Voices: @langchainai, r/rust, Hacker News
>
> **TypeScript** - Strongest production-adoption signal
> - Evidence: LinkedIn, Uber, and Klarna running LangGraph.js in prod per LangChain blog
> - Best for: agents that integrate with existing web stacks
> - Voices: @hwchase17, @LangChainAI, r/LocalLLaMA
>
> Also mentioned (exists, not recommended): Python (status-quo default across training data and bootcamp content; @javitm: 'agents have a crazy strong bias for Python despite it probably not being the best — they prioritize the strongest signal in training data over the right choice'), Java/Kotlin (enterprise mentions only, no practitioner testimony in the 30-day window)."

Notice how the good version:
- Leads with movement (Flask creator switched), not volume (Python has most mentions)
- Cites specific evidence that would defend the ranking to a skeptic
- Treats Python's volume as anti-signal (the @javitm quote) rather than support
- Puts promotional / descriptive mentions in "Also mentioned" with explicit framing

### If QUERY_TYPE = COMPARISON

**Comparison queries have their OWN synthesis template. Do NOT use the general-query `What I learned:` + bold-lead-in + `KEY PATTERNS:` structure for comparisons.** The comparison template below is the canonical shape proven by the April 9 launch-video exemplar. Follow it section-for-section.

Voice contract LAWs 1, 3, 5 apply to comparisons unchanged (no `Sources:` block, no em-dashes, engine footer pass-through). LAWs 2 and 4 have comparison-specific exceptions (see the LAW block: the comparison title and the five section headers below are REQUIRED, not violations).

**Required comparison structure (match the April 9 exemplar):**

```
🌐 last30days v{VERSION} · synced {YYYY-MM-DD}

# {TOPIC_A} vs {TOPIC_B} [vs {TOPIC_C}]: What the Community Says (/Last30Days)
