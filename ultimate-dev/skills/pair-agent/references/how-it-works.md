<!-- Moved verbatim from pair-agent/SKILL.md, the
     'how-it-works' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## How it works

Your gstack browser runs a local HTTP server. This skill creates a one-time setup key,
prints a block of instructions, and you paste those instructions into the other agent.
The other agent exchanges the key for a session token, creates its own tab, and starts
browsing. Each agent gets its own tab. They can't mess with each other's tabs.

The setup key expires in 5 minutes and can only be used once. If it leaks, it's dead
before anyone can abuse it. The session token lasts 24 hours.

**Same machine:** If the other agent is on the same machine (like OpenClaw running
locally), you can skip the copy-paste ceremony and write the credentials directly to
the agent's config directory.

**Remote:** If the other agent is on a different machine, you need an ngrok tunnel.
The skill will tell you if one is needed and how to set it up.
