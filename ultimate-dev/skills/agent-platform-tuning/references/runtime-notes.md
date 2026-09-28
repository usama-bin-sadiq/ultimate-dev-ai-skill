<!-- Moved verbatim from agent-platform-tuning/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Runtime notes

This file was adapted to be tool-neutral: it claimed a general scope and was
bound to one tool. The procedure is unchanged; what changed is that a reader on a
different runtime is told what to substitute.

- **pip** — means. One tool's way of doing a step a different runtime may do another way.
- **cloud-cli** — means. One tool's way of doing a step a different runtime may do another way.
Anything marked **means** is an implementation detail of one tool, and a reader
on a different runtime may need a different mechanism for the same step. Anything
marked **subject** means the capability is genuinely about that tool, and a reader
without it should not expect this file to apply.

Each file below is loaded on demand, not at triage. 3 file(s):

- `./data_prep.md` — Data Preparation for Agent Platform Model Tuning. Agent Platform Model Tuning requires training data in JSON Lines (JSONL)
- `./hf_datasets.md` — Huggingface Dataset References. This document provides references for various datasets used in Agent Platform
- `./tuning_guide.md` — Agent Platform Model Tuning Heuristics and Concepts. This guide details the core concepts of fine-tuning and provides heuristics for
