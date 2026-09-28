<!-- Moved verbatim from ship/SKILL.md, the
     'step-0-9-apple-target-detection' section. The split is mechanical: the content is
     unchanged, and it is here so SKILL.md stays the routing
     surface rather than a manual. -->

## Step 0.9: Apple target detection

If the repo has an `.xcodeproj`, `.xcworkspace`, or Swift app package AND the ask
is App Store/TestFlight distribution, **STOP and Read
`~/.claude/skills/gstack/ship/sections/apple-release.md` FIRST**. Store distribution proceeds
through that adapter from the current branch, including a clean base branch.
The branch gate and repository-landing pipeline below apply ONLY to
repository-landing asks, including on Apple repos.
