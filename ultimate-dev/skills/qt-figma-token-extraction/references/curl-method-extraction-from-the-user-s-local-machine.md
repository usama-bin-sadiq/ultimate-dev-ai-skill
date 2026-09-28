<!-- Moved verbatim from qt-figma-token-extraction/SKILL.md, the 'section' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# curl Method — Extraction from the user's local machine

*(Use when: multiple variable modes, and user is comfortable with a terminal)*

**Requires:** Terminal access (curl is built into macOS and Linux; available on Windows 10+), and a Figma Personal Access Token (viewer scope is enough).

**Important:** Complete all steps in this section — especially PAT setup and verification — before running any curl commands. Running curl with an invalid token will create broken output files.

> **Community files are not supported.** The curl commands only work on Figma files that are in your own account (files you own or have been invited to). Community files you are viewing but have not duplicated will return a 403 error. If the user is working from a community file, ask them to duplicate it to their account first: in Figma, open the community file → click **Duplicate to your drafts** → use the duplicated file's URL instead.

### Step 1a — Set up a Figma Personal Access Token

Do this before anything else. Ask the user:

> "Before we run the extraction command, you'll need a Figma Personal Access Token. Do you already have one?"

If yes: proceed to verification (Step 1b).

If no, guide them through creating one:
> 1. Open Figma in your browser or desktop app
> 2. Click your avatar (top-left) → **Settings**
> 3. Go to the **Security** tab
> 4. Scroll to **Personal access tokens** → click **Generate new token**
> 5. Give it any name (e.g. "Claude token export"), set scope to **Viewer**
> 6. Copy the token immediately — Figma only shows it once

### Step 1b — Verify the PAT works before proceeding

If the PAT was recently verified (within the last 90 days), the user can skip this step. Otherwise, ask the user to run this verification command in their terminal:

```bash
curl -H "X-Figma-Token: YOUR_TOKEN" "https://api.figma.com/v1/me"
```

Expected result: a JSON response containing their Figma account email (e.g. `"email": "name@example.com"`).

If the response contains `"status": 403` or `"Invalid token"`: the token is wrong or expired. Ask the user to generate a new one and try again. **Do not proceed to extraction until the verification succeeds.**

### Step 1c — Run the variables extraction

Ask the user to run in their terminal:

```bash
curl -H "X-Figma-Token: YOUR_TOKEN" "https://api.figma.com/v1/files/FILE_KEY/variables/local" -o design-tokens-raw.json
```

This saves the complete raw variable export — all collections, all modes, all values — to `design-tokens-raw.json`.

### Step 1d — Share the result

Once the command completes, ask the user to either:
- Upload `design-tokens-raw.json` to the conversation, or
- Paste its contents into the conversation

Then continue to Step 2 (Text Styles) below.

---
