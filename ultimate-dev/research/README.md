# Research

What this architecture borrows from outside itself, and — more usefully — what it
does not resolve.

Each area below answers the same four questions: what question the area raises
for the kernel, what approaches were considered, what was adopted, what was
rejected, and what remains open. The open-problems sections are the point. An
architecture that claims to have resolved everything it touches is either
unusually well-supported or not reading carefully.

## Areas

| Area | The question it raises |
|---|---|
| [decision-making](decision-making/) | When is more deliberation the right response to uncertainty, and when is it waste? |
| [context-optimization](context-optimization/) | What is the right amount of material to hold to make a good decision? |
| [capability-acquisition](capability-acquisition/) | How does a system obtain a capability it was not built with? |
| [skill-generation](skill-generation/) | What does it take to turn a repeated procedure into a reusable one? |
| [reasoning](reasoning/) | How much inference-time computation is proportionate, and how is it allocated? |
| [verification](verification/) | What makes a result trustworthy, and what does checking actually cost? |
| [recovery](recovery/) | What should a system do when it fails, and why is retry usually the wrong answer? |
| [learning](learning/) | When should a system change itself, and how does it avoid forgetting or corrupting? |

## How to read this directory

**The adopted/rejected split is the useful part.** A design that lists only what
it borrowed reads as a list of dependencies. A design that records what it
considered and refused is telling you where the reasoning has already been done,
and you do not have to redo it.

**Open problems are not TODOs.** They name tensions that are real and currently
unresolved, such as the cost of verification scaling faster than the value of
the result, or the difficulty of validating a generated skill with no ground
truth. Closing one requires evidence, not effort.

**None of this is a citation list.** Where a named approach appears, it appears
because a specific decision followed from it. A reference nobody acted on is
decoration.

## The honest summary

The areas where this architecture is on firmer ground are the ones with clear
precedents: verification discipline, failure classification, and the economics of
delegation. The areas where it is most speculative are learning and skill
generation, because those depend on a model of long-horizon self-modification
that nobody has validated at the scale this design assumes.

`evaluation/` exists because of that asymmetry. It is weighted toward the claims
that are easiest to get wrong and hardest to notice: over-orchestration on easy
tasks, fabricated tool results, uncontrolled skill proliferation, and learning
installed from a single instance.
