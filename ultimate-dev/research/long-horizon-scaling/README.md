# Long-horizon scaling

What the evidence says about keeping an agent coherent, planned, and stopped
across long, unfamiliar, multi-domain work — and where it contradicts the
kernel's central claim that one machinery scales from L1 to L7 with no separate
serious mode.

## What I could and could not verify

**Accessed and read (primary source, fetched directly).** Where a claim below
rests on one of these, the URL is given inline.

- Context rot (Chroma, 18 models) — https://research.trychroma.com/context-rot
- Lost in the Middle (TACL 2023) — https://arxiv.org/abs/2307.03172
- Anthropic, Effective context engineering (29 Sep 2025) — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, Building effective agents (19 Dec 2024) — https://www.anthropic.com/research/building-effective-agents
- Anthropic, How we built our multi-agent research system (13 Jun 2025) — https://www.anthropic.com/engineering/multi-agent-research-system
- Cognition, Don't Build Multi-Agents (12 Jun 2025) — https://cognition.ai/blog/dont-build-multi-agents
- RULER (COLM 2024) — https://arxiv.org/abs/2404.06654
- MemGPT — https://arxiv.org/abs/2310.08560
- Agentic Context Engineering / ACE (ICLR 2026) — https://arxiv.org/abs/2510.04618
- PlanBench (NeurIPS 2023 D&B) — https://arxiv.org/abs/2206.10498
- ReWOO — https://arxiv.org/abs/2305.18323
- Learning When to Plan — https://arxiv.org/abs/2509.03581
- Fresh Memory, Stale Plans (PlanFence) — https://arxiv.org/abs/2609.03340
- Towards a Science of Scaling Agent Systems (Google/MIT, full HTML read) — https://arxiv.org/abs/2512.08296
- Why Do Multi-Agent LLM Systems Fail? (MAST) — https://arxiv.org/abs/2503.13657
- BAGEN: Are LLM Agents Budget-Aware? — https://arxiv.org/abs/2606.00198
- Budget-Aware Tool Use Enables Effective Agent Scaling (COLM 2026) — https://arxiv.org/abs/2511.17006
- s1: Simple test-time scaling (budget forcing) — https://arxiv.org/abs/2501.19393
- Bounded Rationality for LLMs: Satisficing Alignment (ICML 2025) — https://arxiv.org/abs/2505.23729
- LLMs Cannot Self-Correct Reasoning Yet (ICLR 2024) — https://arxiv.org/abs/2310.01798
- METR, Measuring AI Ability to Complete Long Software Tasks (NeurIPS 2025) — https://arxiv.org/abs/2503.14499
- The Illusion of Diminishing Returns (ICLR 2026) — https://arxiv.org/abs/2509.09677
- Evidence for Limited Metacognition in LLMs (ICLR 2026) — https://arxiv.org/abs/2509.21545
- Agentic Knowledgeable Self-awareness / KnowSelf (ACL 2025) — https://aclanthology.org/2025.acl-long.619/
- TheAgentCompany — https://arxiv.org/abs/2412.14161
- GAIA — https://arxiv.org/abs/2311.12983
- AI Agents That Matter (Kapoor et al.) — https://arxiv.org/abs/2407.01502

**Abstract-level only (identified via search; I did not fetch the full page).**
Claims from these are limited to what the abstract states. Treat the numbers as
unverified against the paper body.

- LLM+P / PDDL world models — https://arxiv.org/abs/2305.14909
- Agentic Benchmark Checklist (ABC) — https://arxiv.org/abs/2507.02825
- Agent Planning Benchmark (APB) — https://arxiv.org/abs/2606.04874

**Failed fetches.**

- https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
  — **failed.** The fetch tool rejected it: `Unsupported fetched file content
  type: application/pdf`. I have not read OpenAI's practical guide and make no
  claims from it. Everything attributed to OpenAI below comes from other
  sources quoting or measuring it, and is marked as such.
- https://arxiv.org/abs/2210.07229 — **resolved, but to the wrong paper.** I
  guessed this ID for LLM+P; it is *Mass-Editing Memory in a Transformer*
  (MEMIT). Corrected to 2305.14909. No conclusion is drawn from 2210.07229.

**Things I looked for and did not find.**

- **No study of whether context rot plateaus.** Chroma reports performance
  "consistently degrades" with length across 18 models and does not test for a
  floor or plateau. This is an open problem, not a settled finding — see
  `## Open problems`.
- **No paper applying satisficing vs. optimising to agent *effort
  allocation*.** The nearest things are SITAlign (satisficing as an inference
  time decoding objective, for alignment) and BAVT / Budget Tracker (budget
  allocation without the satisficing framing). I did not find work that tests
  "stop at good enough rather than optimise" as an agent stopping rule.
- **No source that tests the kernel's central claim directly.** Nobody has
  published a controlled comparison of one agent lifecycle across task scales
  showing the lifecycle is scale-invariant. The claim is an argument, not a
  result. That is stated plainly because it changes how much weight the rest of
  the document can bear.

**Marked as inference.** Statements tagged *(inference)* are mine, derived from
the cited primary source, not made by it.

---

## A. Long-horizon context management

### State of the art

Three mechanisms are in production use, and the sources agree they are
complementary rather than competing.

**Compaction.** Anthropic describes it as "the first lever in context
engineering to drive better long-term coherence": take a conversation near the
limit, summarise, and reinitiate a context window with the summary. In Claude
Code the model preserves "architectural decisions, unresolved bugs, and
implementation details while discarding redundant tool outputs or messages,"
then continues with the compressed context plus the five most recently accessed
files (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

**Structured external note-taking.** Persist notes outside the window and pull
them back later. The cited evidence is Claude playing Pokémon maintaining
"precise tallies across thousands of game steps" and reading its own notes to
continue multi-hour sequences after a context reset
(https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

**Just-in-time retrieval against identifiers rather than content.** Agents hold
lightweight references (paths, queries, links) and load data at runtime, which
also supplies "progressive disclosure" and frees working memory
(https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).

**Sub-agent isolation** as a fourth mechanism is covered in section C.

The formal ancestor of the note/identifier pattern is MemGPT, which frames it as
virtual context management borrowing from OS memory tiers, and evaluates it on
document analysis exceeding the window and multi-session chat
(https://arxiv.org/abs/2310.08560). ACE (ICLR 2026) adds the failure mode the
kernel's learning story needs: iterated rewriting of context causes **context
collapse**, and naive brevity causes **brevity bias**, which drops domain
insights. ACE's fix is structured incremental updates — generate, reflect,
curate — reporting +10.6% on agents and +8.6% on finance
(https://arxiv.org/abs/2510.04618).

### What decides what to drop versus keep

There is a defensible policy, and it is *procedural*, not a scoring function.

Anthropic's ordering is explicit: "Start by maximizing recall to ensure your
compaction prompt captures every relevant piece of information from the trace,
then iterate to improve precision by eliminating superfluous content"
(https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).
They then name the safest first cut: **tool result clearing** — "once a tool has
been called deep in the message history, why would the agent need to see the raw
result again?"

Chroma's LongMemEval experiment supplies the empirical reason. Focused inputs
(~300 tokens) beat full inputs (~113k tokens) across every model family tested,
because full input forces the model to do retrieval and reasoning in one call.
Adding irrelevant context "adds the additional step of identifying what is
relevant, forcing the model to perform two tasks simultaneously"
(https://research.trychroma.com/context-rot).

RULER independently found that models with 200K advertised context "reveal large
room for improvement as we increase input length and task complexity," with
multi-hop tracing and aggregation degrading far more than single-needle
retrieval (https://arxiv.org/abs/2404.06654).

So the policy is: **drop by class, not by score.** Drop raw tool output first,
drop duplicated and superseded material, drop material whose requirement has
closed. Retain decisions, unresolved items, and the criteria verification
depends on. Ranking by "bearing on the live decision" — which the kernel's
context-optimization README already adopts — is consistent with this, but no
source I read provides a validated way to compute it.

### Lost in the middle — and a direct correction

The original finding: performance "is often highest when relevant information
occurs at the beginning or end of the input context, and significantly degrades
when models must access relevant information in the middle of long contexts,
even for explicitly long-context models" (https://arxiv.org/abs/2307.03172).

**The kernel's placement rule is not supported by the strongest available
test.** Chroma extended NIAH across 18 models, 8 input lengths, and 11 needle
positions, and reports: "we find no notable variation in performance for this
specific NIAH task" with respect to needle position
(https://research.trychroma.com/context-rot). They explicitly held the
needle-question pair fixed and varied only irrelevant content, isolating length
as the cause.

What Chroma *does* find is a different driver:

- **Lower needle-question similarity degrades faster.** "As needle-question
  similarity decreases, model performance degrades more significantly with
  increasing input length."
- **Distractors have non-uniform, compounding effect.** "Even a single
  distractor reduces performance relative to the baseline," and the
  non-uniformity "amplifies as input length grows." Distractors 2 and 3 in their
  setup appeared most frequently in hallucinated responses.
- **Model families differ under ambiguity.** Claude Sonnet 4 and Opus 4 "are
  particularly conservative and tend to abstain when uncertain"; GPT models
  "show the highest rates of hallucination, often generating confident but
  incorrect responses when distractors are present."
- **Structural coherence in the surrounding material *hurts*.** Across all 18
  models, "models perform better on shuffled haystacks than on logically
  structured ones." Counterintuitive, and unexplained — Chroma says the
  mechanism is out of scope and would need interpretability work.

*(Inference)* The practical rule that survives is not "put the live decision at
the edge." It is "minimise semantically near-miss material." A coherent,
on-topic, well-written body of context is *more* dangerous than noise, because it
is full of plausible near-misses.

### Does context rot plateau?

**Unknown.** Chroma finds consistent degradation with length across all
experiments and offers no floor (https://research.trychroma.com/context-rot).
Anthropic supplies a shape but not an asymptote: context rot "creates a
performance gradient rather than a hard cliff: models remain highly capable at
longer contexts but may show reduced precision for information retrieval and
long-range reasoning" (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).
A gradient, not a cliff, and not a plateau.

One further observation that complicates a simple length story: in the
Repeated Words replication task, the degradation curve is **not monotone in
output**. Sonnet 3.5 outperforms newer Claude models up to its 8,192-token
output cap, and GPT-4 Turbo shows a local performance peak around 500 words
(https://research.trychroma.com/context-rot). *(Inference)* Degradation with
length is real but interacts with output limit and model generation in ways that
are not yet characterised, which is a further reason not to treat a length
heuristic as a settled mechanism.

---

## B. Planning and decomposition at scale

### What actually works

**Formalisation helps, but not where you would expect.** LLM+P's insight is
that LLMs "while incapable of the combinatorial search needed to produce correct
plans, may be better suited as the source of world models." GPT-4 produced
high-quality PDDL models for 40+ actions which, once corrected, solved 48
challenging planning tasks (https://arxiv.org/abs/2305.14909).

This inverts the usual plan-first intuition. The valuable artifact is the
**precondition/effect model**, not the sequence. And it is corroborated by
PlanBench, which found that "on many critical capabilities — including plan
generation — LLM performance falls quite short, even with the SOTA models"
(https://arxiv.org/abs/2206.10498). PlanBench's motivating observation is
methodological and applies to the kernel's evaluation design: "most claims about
LLM planning capabilities are however based on common sense tasks — where it
becomes hard to tell whether LLMs are planning or merely retrieving from their
vast world knowledge."

**Decoupling plan from observation is a real efficiency win.** ReWOO detaches
reasoning from tool observations, reporting 5× token efficiency and 4% accuracy
improvement on HotpotQA, plus "robustness under tool-failure scenarios"
(https://arxiv.org/abs/2305.18323). Decoupling planning and execution is now
common enough that one paper describes it as "validated through numerous
paradigms" (Devil's Advocate, https://arxiv.org/html/2405.16334v2 — abstract/
body via search, not fetched in full).

**Always planning is worse than never planning.** This is the sharpest
correction in this section. Learning When to Plan: "existing methods like ReAct
prompt LLMs to explicitly plan before every action; however, we demonstrate
that always planning is computationally expensive and degrades performance on
long-horizon tasks, while never planning further limits performance"
(https://arxiv.org/abs/2509.03581). Their zero-shot results show an optimal
**"Goldilocks" planning frequency** rather than a monotone one, and trained
agents learn to "plan when necessary and replan only when necessary,"
discarding plans via adaptive replanning 41% of the time versus 35% for the
SFT-only agent.

*(Inference)* A kernel whose plan is mandatory at every level spends compute
where the evidence says it is actively harmful. L1 should have *zero* planning
steps, and the plan artifact should be something the lifecycle produces on
demand, not a phase it always enters.

### Plan staleness and replanning triggers

**Freshness is not validity.** The most useful paper found on this is PlanFence.
It defines stale-plan execution as the case where "a planner may derive an
action from requirement r₃, another agent may commit r₄, and an executor may
receive r₄ without replacing the plan derived from r₃. … state freshness does
not establish that the plan authorizing an action remains valid." The mechanism
is dependency-scoped validation: "Plans cite the exact public records they used,
and an executor validates only the records that can affect the pending external
action, replanning once or blocking when validation is incomplete."

The result is stark: in 30 controlled live workflows with a post-plan revision,
"a freshness-only executor acts on the obsolete plan in every task, whereas
PlanFence completes all tasks without an invalid action"
(https://arxiv.org/abs/2609.03340).

Two honest qualifications from the authors: the results are "controlled safety
and systems-cost results, not general task-accuracy gains," and the comparison
of proactive synchronisation against scoped validation is conditional — proactive
sync has lower coordination stall at low churn, while scoped validation avoids
repeated update-path coordination as churn grows.

The kernel says its plan is "expected to change when observation contradicts
it." That is a *trigger*. PlanFence's finding is that trigger-based revision is
insufficient because a contradiction may invalidate a unit the agent is not
currently looking at. The missing mechanism is a **citation and scope** rule, not
a better trigger.

Replanning triggers that do have support, all from Learning When to Plan
(https://arxiv.org/abs/2509.03581): a drop in the expected value of the current
subplan, a change in the environment that invalidates a step's precondition, and
completion of a milestone that changes what the remaining work is.

### Tracking dependencies and partial completion

**There is no representation with strong evidence behind it.** The honest
finding.

What exists:

- Anthropic's LeadResearcher "saving its plan to Memory to persist the
  context, since if the context window exceeds 200,000 tokens it will be
  truncated and it is important to retain the plan"
  (https://www.anthropic.com/engineering/multi-agent-research-system).
- Anthropic's pattern of "summariz[ing] completed work phases and stor[ing]
  essential information in external memory before proceeding to new tasks,"
  with fresh subagents spawned at context limits and continuity carried by
  careful handoffs
  (https://www.anthropic.com/engineering/multi-agent-research-system).
- PlanFence's record-citation, which is the only *mechanistic* dependency
  representation found, and it is scoped to "distributed LLM-agent teams" and
  validated on 30 workflows (https://arxiv.org/abs/2609.03340).
- A DAG of sub-questions with automatic context propagation and
  verification-driven adaptive replanning (VMAO, https://arxiv.org/abs/2603.11445
  — abstract only, via search, 25 expert-curated market-research queries, 1–5
  scale, not fetched in full). Treat this as weak evidence.

A knowledge-graph-style store (generative agents,
https://arxiv.org/abs/2304.03442, cited in Cognition's post but not fetched by
me) is the other common answer, and I found no controlled evidence that it beats
a flat unit list with citations. *(Inference)* For the kernel's atomic work units,
PlanFence-style record citation is the cheapest representation that has any
evidence behind it, and it is orthogonal to the unit list already in the design.

---

## C. Multi-agent and subagent orchestration

This is the section with the most direct evidence against the kernel, and the
most direct evidence for it. Both are below, unhedged.

### Evidence FOR delegation

- **Anthropic's production result.** A multi-agent system with Opus 4 leading
  and Sonnet 4 subagents "outperformed single-agent Claude Opus 4 by 90.2% on
  our internal research eval," specifically on "breadth-first queries that
  involve pursuing multiple independent directions simultaneously"
  (https://www.anthropic.com/engineering/multi-agent-research-system).
- **The mechanism is token volume, mostly.** On BrowseComp, three factors
  explain 95% of variance, and "token usage by itself explains 80% of the
  variance, with the number of tool calls and the model choice as the two other
  explanatory factors" (same source). Subagents "scale token usage for tasks that
  exceed the limits of single agents."
- **The scaling study's positive tail.** Relative to a single-agent baseline:
  **+80.8%** on decomposable financial reasoning under centralised
  coordination, and **+9.2%** for decentralised coordination on dynamic web
  navigation — "tasks requiring parallel exploration of high-entropy search
  spaces" (https://arxiv.org/abs/2512.08296).
- **Context isolation works as claimed.** Each subagent may "explore
  extensively, using tens of thousands of tokens or more, but returns only a
  condensed, distilled summary of its work (often 1,000-2,000 tokens)"
  (https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents).
- **Independent parallelism on non-agentic tasks.** 89% on HumanEval with five
  agents, via ensemble/voting effects (https://arxiv.org/abs/2512.08296,
  reporting prior work). This is *not* agentic evidence and should not be
  confused with it.

### Evidence AGAINST delegation

**1. It is 15× the tokens.** "In our data, agents typically use about 4× more
tokens than chat interactions, and multi-agent systems use about 15× more tokens
than chats. For economic viability, multi-agent systems require tasks where the
value of the task is high enough to pay for the increased performance"
(https://www.anthropic.com/engineering/multi-agent-research-system).

**2. The benefit is regime-dependent, and the regimes are wide.** Across 260
configurations, six benchmarks, five architectures and three model families:

- **Capability ceiling.** "Tasks where single-agent performance already exceeds
  **45% accuracy** experience negative returns from additional agents, as
  coordination costs exceed diminishing improvement potential" (β=−0.236,
  p=0.004).
- **Sequential work is actively harmed.** "All multi-agent variants universally
  degrade performance on tasks requiring sequential constraint satisfaction
  (planning: −39% to −70%)". The headline swing is "+80.8% … to −70.0%."
- **Tool-heavy work pays a tax.** "Tool-heavy tasks (e.g., 16-tool business
  workflows) suffer from multi-agent coordination overhead, with efficiency
  penalties compounding as environmental complexity increases" (β=−0.096,
  p=0.002). Mechanism given: multi-agent systems "fragment the per-agent token
  budget, leaving insufficient capacity for complex tool orchestration."
- **Errors amplify without a verification bottleneck.** Independent systems
  "amplify trace-level errors **17.2×** through unchecked error propagation";
  centralised coordination "contains this to **4.4×** by enforcing validation
  bottlenecks that intercept errors before aggregation."

All from https://arxiv.org/abs/2512.08296.

**3. Context fragmentation is the mechanism, and it is not optional.** The same
paper frames it as "an intrinsic information fragmentation … an unavoidable
coordination tax in which the global context must be compressed into
inter-agent messages. This lossy communication increases synchronization
overhead." It reports agents reaching only "34% overlap after 10 interactions"
of world state (reported in 2512.08296, attributed there to prior work).

**4. Two principles that rule out architectures by default.** Walden Yan's
post states them as the basis for "a theory of building long-running agents":

> *Share context, and share full agent traces, not just individual messages.*
> *Actions carry implicit decisions, and conflicting decisions carry bad results.*

And then: "Principles 1 & 2 are so critical, and so rarely worth violating, that
you should by default rule out any agent architectures that don't abide by them"
(https://cognition.ai/blog/dont-build-multi-agents). The stated failure is
subagents each making uncoordinated implicit decisions, producing mutually
inconsistent artifacts that the aggregator then has to reconcile.

On when subagents *are* right, the post is specific: "Claude Code … never does
work in parallel with the subtask agent, and the subtask agent is usually only
tasked with answering a question, not writing any code. Why? The subtask agent
lacks context from the main agent that would otherwise be needed to do anything
beyond answering a well-defined question. The benefit of having a subagent in
this case is that all the subagent's investigative work does not need to remain
in the history of the main agent."

And on multi-agent: "agents today are not quite able to engage in this style of
long-context proactive discourse with much more reliability than you would get
with a single agent."

**5. Duplicated work is the documented early failure mode.** Anthropic's lead
agent was initially given short instructions like "research the semiconductor
shortage," and "found these instructions often were vague enough that
subagents misinterpreted the task or performed the exact same searches as other
agents. For instance, one subagent explored the 2021 automotive chip crisis
while 2 others duplicated work investigating current 2025 supply chains, without
an effective division of labor" (https://www.anthropic.com/engineering/multi-agent-research-system).
They also had agents "spawning 50 subagents for simple queries."

**6. A failure taxonomy exists and is not reassuring.** MAST-Data is 1,600+
annotated traces across 7 MAS frameworks, with 14 failure modes in 3 categories:
system design issues, inter-agent misalignment, and task verification. The
headline is that "their performance gains on popular benchmarks are often
minimal," and that the identified failures "require more sophisticated
solutions" (https://arxiv.org/abs/2503.13657).

**7. Coding is a bad fit, by the vendor that ships it.** "Some domains that
require all agents to share the same context or involve many dependencies
between agents are not a good fit for multi-agent systems today. For instance,
most coding tasks involve fewer truly parallelizable tasks than research, and
LLM agents are not yet great at coordinating and delegating to other agents in
real time" (https://www.anthropic.com/engineering/multi-agent-research-system).

### Where that leaves the kernel's six roles

*(Inference, but it follows directly from the above.)* The evidence supports a
sharp split that the kernel's current framing does not draw:

| Role | Verdict | Basis |
|---|---|---|
| verifier | **Load-bearing**, and only with an external oracle | 17.2× → 4.4× from centralised validation (2512.08296); ICLR 2024 self-correction without external feedback *degrades* performance (2310.01798) |
| investigator | **Supported** — the Claude Code pattern | Context isolation, read-only, answering a well-defined question (anthropic.com/engineering/effective-context-engineering-for-ai-agents; cognition.ai/blog/dont-build-multi-agents) |
| critic, grader, comparator | **Supported**, read-only, cheap | Consistent with the read-only finding; no direct study found |
| author | **Dangerous as designed** | Implicit-decision conflict; requires shared full traces, which defeats context isolation (cognition.ai/blog/dont-build-multi-agents) |

So the design rule the evidence supports is: **delegate for reading, not for
deciding.** A delegated writer that does not see the orchestrator's full trace
is a fresh, uninformed decision-maker — which is the documented failure.

### The honest synthesis

Delegation pays when **all four** hold: the task decomposes into genuinely
independent parts; the material exceeds one context window; the parts do not
need shared context to be done well; and the orchestrator can verify. It loses
when the task is sequential, tool-heavy, or the single agent is already above
roughly 45%. Anthropic's own summary: multi-agent systems "excel at valuable
tasks that involve heavy parallelization, information that exceeds single context
windows, and interfacing with numerous complex tools" — and note that the third
condition is in tension with the scaling study's tool-heavy tax.

---

## D. Knowing when to stop

### The headline: unmanaged budget does nothing

"Simply increasing the tool-call budget fails to improve performance, as agents
lack 'budget awareness' and quickly hit a performance ceiling." The fix is a
lightweight Budget Tracker providing continuous awareness, which then enables
BATS to "dynamically adapt its planning and verification strategy." Reported
effect: "budget-aware methods produce more favorable scaling curves and push the
cost-performance Pareto frontier" (https://arxiv.org/abs/2511.17006, COLM 2026).

This is the single most direct challenge to a scale ladder that treats resources
as the lever. More budget alone is not neutral — it is wasted, and it is wasted
*while the agent looks productive*.

### Budget awareness is a separate, weak, measurable capability

BAGEN formalises it as "progressive interval estimation: at each step of a plan,
an agent should predict an upper and lower bound on remaining budget, and alert
when completion is unlikely," scored by replaying logged prefixes. Four
findings, all from https://arxiv.org/abs/2606.00198:

1. "Strong agents do not necessarily have strong budget-awareness, with
   correlation **r=0.35**." Capability and budget sense are different things.
2. "Frontier models are consistently **over-optimistic**, continue spending on
   tasks that are unlikely to succeed, instead of alerting the user early."
3. "Early stop saves **28–64% of tokens** on failed trajectories, and SFT+RL
   strengthens early stop and alert behavior."
4. "Precise interval calibration remains challenging, with interval coverage
   capping at **47%** after SFT+RL."

### Termination mechanisms that exist

- **Hard iteration cap.** Anthropic's baseline recommendation: "it's also common
  to include stopping conditions (such as a maximum number of iterations) to
  maintain control" (https://www.anthropic.com/research/building-effective-agents).
- **Budget forcing.** s1 forcefully terminates thinking when the budget is
  reached, or extends it by appending "Wait" — which "can lead the model to
  double-check its answer, often fixing incorrect reasoning steps." Scaling s1
  from 50% to 57% on AIME24 by budget alone
  (https://arxiv.org/abs/2501.19393). A later comparison reports budget guidance
  as 37% faster and 26% more accurate than budget forcing, with 100% of
  under-budget samples still correct (https://aclanthology.org/2026.findings-acl.1866.pdf
  — abstract-level via search, not fetched).
- **Value-threshold stopping with three regimes.** Terminate when value exceeds
  a threshold τ; explore laterally when the last action yielded zero or negative
  information gain; deepen when it yielded positive gain below τ. The paper
  shows termination with probability ≥ 1−ε under an explicit budget guarantee
  (BAVT, https://arxiv.org/pdf/2603.12634 — via search, not fetched in full).
- **Consensus / quality thresholds** set by the orchestrator
  (https://arxiv.org/abs/2512.08296, orchestration-policy definition).
- **Anthropic's scaling rules as a heuristic.** "Simple fact-finding requires
  just 1 agent with 3-10 tool calls, direct comparisons might need 2-4 subagents
  with 10-15 calls each, and complex research might use more than 10 subagents
  with clearly divided responsibilities. These explicit guidelines help the lead
  agent allocate resources efficiently and prevent overinvestment in simple
  queries, which was a common failure mode"
  (https://www.anthropic.com/engineering/multi-agent-research-system).

### Avoiding both infinite loops and premature stopping

The evidence gives an asymmetry, and it favours stopping early. Frontier models
are systematically over-optimistic about remaining budget (BAGEN), so a
continuing agent is more likely to be burning budget on a doomed task than
stirring the pot. Meanwhile self-correction without external feedback *reduces*
accuracy (https://arxiv.org/abs/2310.01798), so "keep trying, you'll get it" is
not a safe default either.

*(Inference)* The defensible composite is: a hard cap as a backstop, plus a
periodic feasibility check that requires an **external** signal, plus an explicit
stagnation rule keyed on information gain rather than on elapsed steps. A run
that has produced no new information for N steps has met its definition of stuck,
and step count is a poor proxy — BAGEN's optimistic bias means agents will happily
exceed any step budget you set.

### Satisficing vs optimising

**No direct work on satisficing as an agent effort-allocation rule was found.**
What exists:

- SITAlign operationalises satisficing for *alignment* at inference time —
  "maximizing a primary objective while satisfying threshold-based constraints
  on secondary criteria" — with sub-optimality bounds and a 22.3% margin over a
  SOTA multi-objective decoding strategy on helpfulness under a harmlessness
  threshold (ICML 2025, https://arxiv.org/abs/2505.23729). The mechanism
  transfers; the objective does not.
- BAVT implements the *shape* of satisficing: "when resources are abundant, the
  framework encourages broad exploration… as the budget depletes, the framework
  aggressively transitions into greedy exploitation"
  (https://arxiv.org/pdf/2603.12634, via search).
- Cost-aware stopping has a clean decision rule: "Stopping is optimal exactly
  when continuing cannot do better, i.e., when Δ(Sₜ) ≥ 0… continuing is preferred
  if and only if Vₜ₊₁ − Vₜᶜⱼ ≥ λ"
  (https://arxiv.org/pdf/2607.27083v1, via search).

*(Inference)* The transferable idea is **threshold-on-secondary-criteria
degrading into threshold-on-primary-criterion** as budget falls. That is a
satisficing policy for effort, and it is not the same as "stop when it looks
good enough," which is what the kernel's verification discipline currently
implies.

### The external bound on all of this

METR's 50%-task-completion time horizon was "around 50 minutes" for Claude 3.7
Sonnet, doubling roughly every seven months since 2019, "though the trend may
have accelerated in 2024." The mechanism is identified as "greater reliability and
ability to adapt to mistakes, combined with better logical reasoning and tool use"
(https://arxiv.org/abs/2503.14499). TheAgentCompany: the most competitive agent
completes **30%** of workplace tasks autonomously; "a good portion of simpler
tasks could be solved autonomously, but more difficult long-horizon tasks are
still beyond the reach of current systems" (https://arxiv.org/abs/2412.14161).
GAIA: humans 92% versus GPT-4 with plugins 15% (https://arxiv.org/abs/2311.12983).

---

## E. Domain generality

### Agents in unfamiliar domains, and how they fail

GAIA is the cleanest design for this question, and it is deliberately
anti-benchmark. Its 466 questions are "conceptually simple for humans yet
challenging for most advanced AIs" and it "departs from the current trend in AI
benchmarks suggesting to target tasks that are ever more difficult for humans."
Its stated thesis: "the advent of Artificial General Intelligence hinges on a
system's capability to exhibit similar robustness as the average human does on
such questions" (https://arxiv.org/abs/2311.12983). The failure signature is
therefore *not* inability — it is fragility across heterogeneous task types
where each individual task type is easy.

TheAgentCompany gives the workplace-scale version, and its own summary is
nuanced rather than encouraging: "a good portion of simpler tasks could be solved
autonomously, but more difficult long-horizon tasks are still beyond the reach of
current systems" (https://arxiv.org/abs/2412.14161).

**The most useful decomposition of long-horizon failure is the Illusion of
Diminishing Returns paper**, and it is the finding most likely to change the
kernel. They isolate *execution* by explicitly providing the knowledge and plan
needed for a long-horizon task, then report (https://arxiv.org/abs/2509.09677,
ICLR 2026):

- "Larger models can correctly execute significantly more turns even when small
  models have near-perfect single-turn accuracy."
- "The per-step accuracy of models degrades as the number of steps increases."
- "This is not just due to long-context limitations — curiously, we observe a
  **self-conditioning effect** — models become more likely to make mistakes when
  the context contains their errors from prior turns."
- "Self-conditioning does not reduce by just scaling the model size."
- "Thinking mitigates self-conditioning, and also enables execution of much
  longer tasks in a single turn."
- And the framing result: "even marginal gains in single-step accuracy can
  compound into exponential improvements in the length of tasks a model can
  successfully complete."

Read together with METR, the picture is: **the thing that scales long-horizon
performance is per-step reliability, and per-step reliability degrades partly
because the agent's own past errors are in the context.** That is a mechanism
the kernel does not currently name, and it is not a context-length problem.

### Is there value in an explicit metacognitive / triage step?

**The evidence is that triage is valuable in principle and unavailable in
practice via prompting.**

Against:
- KnowSelf (ACL 2025) tests agentic self-awareness directly and finds
  "**State-of-the-art reasoning models fall short in agentic knowledgeable
  self-awareness through only prompting**… merely prompting the model is far
  from sufficient to acquire these abilities. More efforts are required in terms
  of data, training strategies, and model architecture"
  (https://aclanthology.org/2025.acl-long.619/). Its framing of the status quo
  is the relevant line: traditional approaches "adopt a 'flood irrigation'
  methodology that indiscriminately injects gold trajectories, external feedback,
  and domain knowledge," which "overlooks… the ability to dynamically assess
  situational demands and strategically employ resources during decision-making."
- Ackerman (ICLR 2026) tests whether models can *strategically deploy*
  metacognitive knowledge rather than self-report it, across 18+ models
  including o1 and Claude 4: there is "increasingly strong evidence of certain
  metacognitive abilities," but they are "limited in resolution, emerge in
  context-dependent manners, and seem to be qualitatively different from those
  of humans" (https://arxiv.org/abs/2509.21545). Resolution-limited confidence
  estimation is exactly what a cost-benefit triage decision needs and does not
  have.

For:
- The thinking stage acts as an internal verifier. Reasoning models "surpass
  their instruction-following variants" on self-awareness scoring (+9.3 on
  gemini-3), "consistent with the thinking stage acting as an internal verifier:
  before committing to action, reasoning models reassess whether the task truly
  exceeds their parametric capability" (KAPRO, https://arxiv.org/abs/2606.20661 —
  abstract-level via search, not fetched; cited in
  https://arxiv.org/html/2606.00198v1).
- Illusion of Diminishing Returns independently finds "thinking mitigates
  self-conditioning" (https://arxiv.org/abs/2509.09677). Two independent sources
  converging on deliberation-as-verifier is the strongest pro-triage signal here.

*(Inference)* The kernel's capability-resolution chain (do → existing → compose
→ acquire → create) is a triage procedure whose first step is a
self-assessment. Self-assessment is resolution-limited and optimistic. So the
chain should not be entered by asking the model "can I do this?" It should be
entered by asking questions answerable from structure: does a capability exist,
what does it cost to invoke, is the unit's completion checkable by something
other than judgement. That converts triage from a metacognitive act into a
lookup, which is the only form the evidence supports.

---

## What I should change in my design

Ranked by expected impact. Each names the practice, the source, and the
specific edit.

### 1. Replace "the scale ladder changes resources" with "the scale ladder must select an orchestration topology, and that selection has measured sign flips"

**Source:** https://arxiv.org/abs/2512.08296

The single most consequential correction. The claim "only resources/depth
change, not the lifecycle" is safe as a statement about the *lifecycle* and
unsafe as a statement about the *orchestration*. The evidence shows regimes,
not dials: −70% to −39% on sequential planning, a negative-return threshold at
45% single-agent accuracy (β=−0.236, p=0.004), and a tool-heavy tax
(β=−0.096, p=0.002). These are not resource levels; they are different systems.

**Change to the kernel:** keep the L-ladder, but add a mandatory, separate
decision to the L-transition: *topology selection* over {single-agent
continuous, centralised-verified, decentralised-parallel, independent-ensemble},
with the four measured task properties above (decomposability, sequential
constraint density, tool count, current single-agent competence) as inputs. Add a
new reference file recording the thresholds and their effect sizes with the
arXiv ID, and state in the kernel that topology is a discrete choice the scale
ladder triggers, not a dial the scale ladder turns. The honest reframing is: the
lifecycle is invariant; **the orchestration is not**, and pretending otherwise
is the "separate serious mode" the design claims not to have — it just hides the
mode switch inside the resource dial.

### 2. Add a self-conditioning counter-mechanism; name it as the primary long-horizon failure mode

**Source:** https://arxiv.org/abs/2509.09677

The kernel has no mechanism for "the agent's own prior errors degrade its later
steps, and scaling the model does not fix it." The existing context-optimization
README treats degradation as a function of length and dilution, which this paper
shows is incomplete. It also reframes METR: per-step reliability is the scaling
lever, and reliability is what self-conditioning eats.

**Change to the kernel:** add to the compaction/spec a required distinction
between *external* history (observations, tool output) and *derived* history
(what the agent concluded, including wrong conclusions), with a rule that a
conclusion which a verifier has since contradicted is demoted out of the working
context rather than merely marked. Add an evaluation case that plants a
plausible-wrong early step and measures whether the agent's later steps inherit
it, at L4 and above. Also correct the context-optimization README's open problem
"Context rot is not decomposable" — one part now *is* decomposable: the
self-conditioned portion.

### 3. Demote the lost-in-the-middle placement rule; promote distractor suppression

**Source:** https://research.trychroma.com/context-rot

The kernel's placement rule ("state the live decision near the material it
governs") rests on a positional effect that the strongest available test does
not find: across 18 models, 11 positions, and 8 input lengths, Chroma "find[s] no
notable variation in performance for this specific NIAH task" with respect to
needle position. What Chroma does find is that degradation is driven by semantic
near-miss material and by distractor count and character, and — surprisingly —
that **coherent, well-structured context is worse than shuffled context**.

**Change to the kernel:** change the placement rule in the context-optimization
README from a claim to a hypothesis, and add the mechanism Chroma found: a
check that the live material is not semantically confusable with material already
loaded. The actionable form is not "move it to the edge," it is "remove the
near-misses." Add a reference note recording that the positional effect was not
reproduced on frontier models in this setup, and that structured-but-irrelevant
context is a distinct risk class. This is a case where the existing README is
more confident than its evidence permits, and the fix is to weaken the claim
rather than to defend it.

### 4. Add budget awareness as a first-class, measurable kernel mechanism

**Sources:** https://arxiv.org/abs/2511.17006, https://arxiv.org/abs/2606.00198

Budget-Aware Tool Use: unmanaged budget increases produce a performance ceiling.
BAGEN: strong agents are not budget-aware (r=0.35), are systematically
over-optimistic, and early stop saves 28–64% of tokens on failed trajectories.
The kernel's scale ladder currently treats resources as something more is always
better at. That is false in a specific, measurable way.

**Change to the kernel:** add a "budget position" line to the mutable plan
state, updated at every unit boundary, carrying spent/remaining on the same
units as the context budget. Add a standing rule: when the budget position
cannot be stated in one sentence, the next action is a feasibility check, not
another attempt. Add a stall rule keyed on information gain, not step count,
because BAGEN's optimistic bias means agents will exceed any step cap. Add
evaluation cases asserting (a) that the agent can state remaining budget, and
(b) that it abandons a hopeless branch rather than finishing it. Record in a
reference that interval calibration is weak (coverage caps at 47%), so the
kernel should ask for a *feasibility judgement*, not a numeric estimate.

### 5. Split the six delegated roles into read-only and deciding, and constrain the author role

**Sources:** https://cognition.ai/blog/dont-build-multi-agents,
https://arxiv.org/abs/2512.08296, https://arxiv.org/abs/2503.13657

Cognition's two principles — share full traces; actions carry implicit decisions
— imply that a delegated writer without the orchestrator's trace is an
uninformed decision-maker, and the scaling study quantifies the general shape:
error amplification 17.2× without a validation bottleneck, 4.4× with one.
MAST's 14 failure modes sit in system design, inter-agent misalignment, and task
verification.

**Change to the kernel:** mark investigator, critic, grader, comparator as
read-only-by-construction, and require that their briefs include the
orchestrator's reasoning relevant to the question — not just the task text.
Change **author** from a peer role to a role that either (a) receives the
orchestrator's full trace, or (b) is restricted to a unit whose correctness is
mechanically checkable, in which case the orchestrator does not need its
reasoning. Add a reference file per role stating the admissible topology from
2512.08296, with the +80.8% / −70% numbers attached so the choice is not
motivated. Add an evaluation case that measures duplicated work across sibling
roles, since Anthropic names that as the first real failure.

### 6. Make the mandatory plan conditional, and give plan units declared preconditions and effects

**Sources:** https://arxiv.org/abs/2509.03581, https://arxiv.org/abs/2305.14909,
https://arxiv.org/abs/2206.10498

Learning When to Plan: always planning "degrades performance on long-horizon
tasks," and the zero-shot optimum is a Goldilocks frequency, not a maximum.
LLM+P: the LLM's productive role is producing the *world model* (preconditions
and effects), not the sequence. PlanBench: plan generation "falls quite short,
even with the SOTA models."

**Change to the kernel:** at L1 the plan is empty and that is correct — say so
explicitly in the kernel, because "one lifecycle at every level" currently
implies a plan artifact everywhere. Add two required fields to every atomic work
unit above L2: `precondition` and `expected_effect`, in the unit's own terms.
This is the cheapest available move toward making a unit independently
verifiable by something other than a judge, and it is the part of LLM+P's result
that transfers to a Markdown skill with no runtime.

### 7. Add record citation to plan units, and treat freshness as insufficient

**Source:** https://arxiv.org/abs/2609.03340

A freshness-only executor "acts on the obsolete plan in every task" across 30
controlled workflows. The kernel's "expected to change when observation
contradicts it" is a trigger rule and is not sufficient against a contradiction
elsewhere in the plan.

**Change to the kernel:** each plan unit cites the evidence records it was
derived from; a unit whose cited records have changed is invalidated even if
nothing in the current unit contradicts. Add an evaluation case where a
mid-run revision invalidates a unit the agent is *not* currently working on.
State the paper's own caveat in the reference (30 workflows; safety and
coordination-cost results, not accuracy gains) so the mechanism is not
oversold.

### 8. Require external oracles from the verifier, and forbid bare self-critique

**Sources:** https://arxiv.org/abs/2310.01798, https://arxiv.org/abs/2512.08296

ICLR 2024: LLMs "struggle to self-correct their responses without external
feedback, and at times, their performance even degrades after self-correction."
The scaling study attributes its largest single improvement to centralised
validation, not to more agents.

**Change to the kernel:** the verifier role's spec must require a named external
signal — a test, a tool result, a file state, a user. A verifier that re-reads
the agent's own output is not a verifier. Add a reference note distinguishing
this from the critic role, and add an evaluation case where the verifier is
given only the artifact and no oracle, asserting the kernel does not treat its
verdict as a pass.

### 9. Add a structured triage entry to capability resolution that does not depend on self-assessment

**Sources:** https://aclanthology.org/2025.acl-long.619/,
https://arxiv.org/abs/2509.21545

KnowSelf: SOTA reasoning models "fall short in agentic knowledgeable
self-awareness through only prompting." Ackerman: metacognitive abilities are
resolution-limited and context-dependent. Yet two independent sources find
deliberation acts as an internal verifier and that thinking mitigates
self-conditioning.

**Change to the kernel:** reframe capability resolution as a *lookup with
costing*, not a self-assessment. Each rung is entered on a structural question
(is there a capability, what does invoking it cost, is the unit's completion
externally checkable), never on "can I do this." Record the r=0.35-style
separation explicitly in a reference so the kernel's own capability ladder is
not confused with the model's. Add a deliberation-before-committing rule at L4+
given the two converging findings, but do not rely on it at L1–L2.

### 10. Fix the evaluation suite: report cost, add holdouts, audit the graders

**Sources:** https://arxiv.org/abs/2407.01502, https://arxiv.org/abs/2507.02825,
https://arxiv.org/abs/2412.14161

AI Agents That Matter: "there is a narrow focus on accuracy without attention to
other metrics. As a result, SOTA agents are needlessly complex and costly, and
the community has reached mistaken conclusions about the sources of accuracy
gains." Also: many agent benchmarks "have inadequate holdout sets, and
sometimes none at all," producing agents that "take shortcuts and overfit."
ABC, applied to ten benchmarks, found seven with outcome-validity flaws, seven
with task-validity flaws, and **all** with reporting limitations; the issues can
cause "up to 100% in relative terms" misestimation. TheAgentCompany suggests
the right shape: "focusing on end-state evaluation rather than turn-by-turn
analysis… For complex workflows, break evaluation into discrete checkpoints where
specific state changes should have occurred, rather than attempting to validate
every intermediate step" (https://www.anthropic.com/engineering/multi-agent-research-system).

**Change to the evaluation suite:** (a) every case reports success *and* cost, in
tokens and tool calls, with a Pareto view rather than a single number; (b) every
level of the L-ladder has a held-out set that is never used for tuning; (c) the
kernel's own graders are audited against the ABC outcome-validity items — in
particular whether a "verified" unit can be passed without being completed;
(d) evaluation is at checkpoints, not per step. Item (a) is the one that will
change conclusions fastest, because a 15× token multiplier
(https://www.anthropic.com/engineering/multi-agent-research-system) is invisible
to a success-rate-only suite, and the kernel's whole economic claim rests on
orchestration costs.

### 11. Bound the L7 claim against measured capability, and add graceful-degradation as the design target

**Sources:** https://arxiv.org/abs/2503.14499, https://arxiv.org/abs/2412.14161,
https://arxiv.org/abs/2311.12983

METR: ~50 minutes at the 50% time horizon for Claude 3.7 Sonnet, doubling ~7
monthly. TheAgentCompany: 30% autonomous, with long-horizon tasks explicitly out
of reach. GAIA: 92% human versus 15% GPT-4+plugins on conceptually simple
questions.

**Change to the kernel:** do not assert L7 behaviour. Assert a measurable
property instead: *given a task longer than the model's measured time horizon, the
kernel degrades to a partial, resumable, honestly-labelled result rather than to
a confident wrong one.* Add an evaluation axis that reports the kernel's
time-horizon at which its success rate crosses 50%, so the claim becomes a number
that moves as models improve, and so the design has a defined failure behaviour
before L7 exists. The abstention result in the context-rot report is the
mechanism to lean on here: Claude models "consistently exhibit the lowest
hallucination rates" and "tend to abstain when uncertain" under ambiguity
(https://research.trychroma.com/context-rot) — abstention is measurable, and the
kernel currently has no abstention state.

---

## Open problems

**No source tests the central claim.** No controlled study compares one agent
lifecycle across task scales and shows the lifecycle is scale-invariant. The
kernel's headline is an argument. Everything in the sections above is evidence
about *components* of the claim; none of it validates the composition.

**Does context rot plateau?** Unknown and untested. Chroma shows consistent
degradation and does not probe for a floor. Anthropic describes a gradient, not
a cliff — which is a shape claim, not an asymptote. If there is a plateau, the
whole "keep context small" argument weakens at large scale; if there is not, the
kernel's budget conservatism is right for the wrong reason. Nobody has run the
experiment.

**What is the self-conditioning rate in real agents?** Illusion of Diminishing
Returns isolates it cleanly in controlled execution tasks. Whether it operates at
the same magnitude once the agent also plans, uses tools, and carries a
self-authored plan is unmeasured. The interaction between self-conditioning and
the kernel's own learning mechanism — which deliberately *retains* conclusions —
is the sharpest unexamined risk in the design: gated learning is exactly the
condition under which a wrong conclusion stays in context and is re-read every
step.

**Mutable plan versus decoupled plan.** ReWOO's efficiency and tool-failure
robustness come from a plan fixed up front. The kernel's replanning requires
interleaving. The scaling study's finding that independent systems amplify errors
17.2× suggests the two cannot simply be combined, and I found no work that
resolves it. This is a real architectural fork, not a missing detail.

**Satisficing as an effort-allocation rule does not exist.** The mechanism is
understood (SITAlign, BAVT, cost-aware stopping) but nobody has tested "stop at
good enough" as a stopping rule for agents against "optimise until budget
exhausted," with both measured on the same long-horizon tasks. Given BAGEN's
finding that models are systematically over-optimistic, the interesting version
is not satisficing-versus-optimising but *over*-optimisation-versus-calibrated-
satisficing, and that comparison is unmade.

**What replaces self-correction when the agent is the only oracle?** ICLR 2024
says self-correction without external feedback degrades. The kernel's
verification discipline assumes an oracle exists. For units where no oracle
exists — prose, design decisions, unfamiliar domains — the kernel has no
defensible verification story, and that is precisely the L6–L7 case the kernel
claims to cover.

**Coordination cost at scale is measured; coordination cost *as a function of
scale* is not.** The scaling study has 260 configurations and reports overhead
scaling non-linearly with task complexity via an interaction term, but its
predictive R² is 0.373 (0.413 with a task-grounded capability metric). Its 87%
held-out accuracy is for *architecture selection*, explicitly not for absolute
cross-domain performance prediction. A framework that explains a third of the
variance is useful for choosing a topology and useless for predicting whether a
given programme will work.

**Position effects are model- and task-dependent, and one strong test failed to
reproduce them.** Chroma's null result on needle position across 18 frontier
models contradicts the effect the kernel adopted from a 2023 paper. Whether the
effect is absent, weaker, or present in different tasks is unresolved. The
kernel's open problem "Position effects are borrowed, not measured" is correct
and should be strengthened to "and one direct measurement failed to find them."

**Whether a triage step helps at all, absent training.** Two findings support
deliberation-as-verifier and two refute prompting-only self-awareness. They are
not obviously reconcilable, and no work I found settles it. Given KnowSelf
required SFT+RL to move the needle, the default expectation for a Markdown skill
with no training should be that a triage step costs tokens and returns little —
unless it is structured as a lookup, which is recommendation 9.
