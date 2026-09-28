<!-- Moved verbatim from agent-platform-eval-flywheel/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **pip** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.

Each file below is loaded on demand, not at triage. 5 file(s):

- `./dataset_schema.md` — Evaluation Dataset Schema. Canonical formats for evaluation datasets in the Google GenAI Evaluation SDK.
- `./deployment.md` — Deploying and Evaluating Models on Agent Platform Endpoints. Reference for the deployment-and-endpoint-evaluation subset of the Quality
- `./failure_patterns.md` — Evaluation Failure Patterns & Fixes. Common failure modes observed in GenAI agent evaluations, mapped to their root
- `./metric_registry.md` — GenAI Evaluation Metric Registry. Complete catalog of evaluation metrics available in the agentplatform SDK.
- `./sdk_patterns.md` — Agent Platform Evaluation SDK Patterns. Code patterns for common evaluation scenarios using agentplatform.genai.evals
