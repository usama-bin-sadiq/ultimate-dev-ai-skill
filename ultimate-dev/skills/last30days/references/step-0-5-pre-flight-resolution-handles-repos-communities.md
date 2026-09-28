<!-- Moved verbatim from last30days/SKILL.md, the 'Step 0.5: Pre-Flight Resolution (handles, repos, communities)' section. Relative links were rebased for the new depth; the prose is otherwise unchanged. -->

# Step 0.5: Pre-Flight Resolution (handles, repos, communities)

**Pre-Flight Checklist — do NOT stop after the first flag. Every applicable flag below is MANDATORY for its topic class.**

Before running the engine, determine which flags apply to this topic and resolve them. Reading only the "X handle" subsection and stopping there is the named failure mode of the Peter Steinberger disaster #2 (2026-04-18). The model admitted on debug: "I treated the 'X handle resolution' section as the full contract for pre-flight resolution and didn't --help the script to see what else existed." The checklist below IS the full contract.

| Flag | Resolved in | Applies when |
|------|-------------|--------------|
| `--x-handle={handle}` | Step 0.5 (Section A below) | X is in `ACTIVE_SOURCES_LIST` and the topic is a person, brand, product, or creator with an X presence |
| `--x-related={h1,h2,...}` | Step 0.5 (Section A below) | X is in `ACTIVE_SOURCES_LIST` and the topic has associated entities (founders, commentators, spouse, collaborators, media handles) |
| `--github-user={user}` | Step 0.5b | Topic is a person who ships code (developer, engineer, CEO-who-codes, researcher) |
| `--github-repo={owner/repo}` | Step 0.5c | Topic is a product / project / open-source tool |
| `--trustpilot-domain={domain}` | Step 0.5d | Topic is a company / brand / service with a Trustpilot presence (passing the flag also auto-activates the opt-in Trustpilot source for this run) |
| `--amazon-query={keyword}` | Step 0.5e | Recent buyer sentiment would materially inform the report AND `brightdata` is on PATH and logged in. Keyword is brand-plus-category (`Weber grill`), and for a person topic it is their company's product line (`June Oven`), not their name. Also add `amazon` to `--search` |
| `--meta-ads-page={page_id}` | Step 0.5f | Name-based advertiser resolution picked the wrong company, or the brand advertises only under product-line page names. Accepts a numeric Ad Library page id or an Ad Library URL with `view_all_page_id`; a facebook.com vanity URL is not a page id. Also add `meta_ads` to `--search` |
| `--subreddits={sub1,sub2,...}` | Step 0.55 | Always — almost every topic has active Reddit communities |
| `--tiktok-hashtags={h1,h2,...}` | Step 0.55 | Always — inferred from topic |
| `--tiktok-creators={c1,c2,...}` | Step 0.55 | Creator / influencer / brand topics |
| `--ig-creators={c1,c2,...}` | Step 0.55 | Creator / brand topics |
| `--web-backend brave` | Step 0.45 Class 5 | **MANDATORY** for non-Latin-script topics (Hebrew, Arabic, CJK, etc.) — Brave is the only source that indexes non-English web |
| `--web-backend parallel-mcp` | Explicit user request only | Use only when the user asks to use Parallel Search MCP. This opts the run into sending its search objective and queries to `https://search.parallel.ai/mcp`; never select it automatically. Anonymous use sends no authorization header; an existing `PARALLEL_API_KEY` is sent as Bearer auth. |
| `--auto-resolve` | Fallback | WebSearch is available but Step 0.55 could not resolve everything cleanly — use as belt-and-suspenders |

**Checkpoint before running the engine:** your Bash command must include every flag from the checklist that applies to this topic. For a person who ships code (the Peter Steinberger class), that is MINIMUM `--x-handle` AND `--github-user` AND `--subreddits`, and typically `--x-related` too. A command with only `--x-handle` on a person topic is a pre-flight skip and a Step 0.5 regression.

---

### Section A: Resolve X Handles (only when X is active and the topic could have X accounts)

If `ACTIVE_SOURCES_LIST` contains `x` and TOPIC looks like it could have its own X/Twitter account - **people, creators, brands, products, tools, companies, communities** (e.g., "Dor Brothers", "Jason Calacanis", "Nano Banana Pro", "Seedance", "Midjourney"), do WebSearches to find handles in three categories. If X is not active, skip this section without prompting or trying to unlock it.

**1. Primary handle** (the entity itself):
```
WebSearch("{TOPIC} X twitter handle site:x.com")
```

**2. Company/organization handle OR founder/creator handle** -- This mapping is bidirectional:
- If the topic is a **PERSON**, resolve their company's X handle. A CEO's story is inseparable from their company's story.
- If the topic is a **PRODUCT or COMPANY**, resolve the founder/creator's personal X handle. The creator's personal account often has the most candid, high-signal content.
```
WebSearch("{TOPIC} company CEO of site:x.com")
```
OR for products:
```
WebSearch("{TOPIC} creator founder X twitter site:x.com")
```
Examples: Sam Altman -> @OpenAI, Dario Amodei -> @AnthropicAI, OpenClaw -> @steipete (Peter Steinberger), Paperclip -> @dotta, Claude Code -> @alexalbert__.

**3. 1-2 related handles** -- People/entities closely associated with the topic (spouse, collaborator, band member), PLUS 1-2 prominent commentator/media handles that regularly cover this topic:
```
WebSearch("{RELATED_PERSON_OR_ENTITY} X twitter handle site:x.com")
```
For a music artist, find music commentary accounts (e.g., @PopBase, @HotFreestyle, @DailyRapFacts).
For a tech CEO, find tech media accounts (e.g., @TechCrunch, @TheInformation).
For a product, find reviewer accounts in that category.

From the results, extract their X/Twitter handles. Look for:
- **Verified profile URLs** like `x.com/{handle}` or `twitter.com/{handle}`
- Mentions like "@handle" in bios, articles, or social profiles
- "Follow @handle on X" patterns

**Verify accounts are real, not parody/fan accounts.** Check for:
- Verified/blue checkmark in the search results
- Official website linking to the X account
- Consistent naming (e.g., @thedorbrothers for "The Dor Brothers", not @DorBrosFan)
- If results only show fan/parody/news accounts (not the entity's own account), skip - the entity may not have an X presence

Pass handles to the CLI:
- Primary: `--x-handle={handle}` (without @)
- Related: `--x-related={handle1},{handle2},{company_handle},{commentator_handles}` (comma-separated, without @)

Example for "Kanye West":
- Primary: `--x-handle=kanyewest`
- Related: `--x-related=travisscott,PopBase,HotFreestyle`

Example for "Sam Altman":
- Primary: `--x-handle=sama`
- Related: `--x-related=OpenAI,TechCrunch`

Related handles are searched with lower weight (0.3) so they appear in results but don't dominate over the primary entity's content.

**Note about @grok:** Grok is Elon's AI on X (xAI). It often appears in search results with thoughtful, accurate analysis. When citing @grok in your synthesis, frame it as "per Grok's AI analysis of [article/topic]" rather than treating it as an independent human commentator.

**Skip this step if:**
- TOPIC is clearly a generic concept, not an entity (e.g., "best rap songs 2026", "how to use Docker", "AI ethics debate")
- TOPIC already contains @ (user provided the handle directly)
- Using `--quick` depth
- WebSearch shows no official X account exists for this entity

Store: `RESOLVED_HANDLE = {handle or empty}`, `RESOLVED_RELATED = {comma-separated handles or empty}`

### Step 0.5b: Resolve GitHub Username (if topic is a person) — MANDATORY FOR PERSON TOPICS

**MANDATORY when the topic is a person (developer, creator, CEO, founder, engineer, researcher) and WebSearch is available.** Resolving the X handle but NOT the GitHub handle is the documented Peter Steinberger failure mode (2026-04-18). Without `--github-user={handle}`, GitHub search becomes a keyword match across all of GitHub instead of person-mode scoped to `user:{handle}`. The result is typically 5-10 thin unrelated items instead of the person's actual commits, PRs, releases, and top-starred repos. Treat this as a peer step to Step 0.5 (X handle resolution), not an afterthought.

Do the WebSearch:

```
WebSearch("{TOPIC} github profile site:github.com")
```

From the results, extract their GitHub username from URLs like `github.com/{username}`.

**Verify the account is correct:** Check that the profile description or pinned repos match the person you're researching. Common names may return multiple profiles.

Pass to the CLI: `--github-user={username}` (without @)

Worked examples:
- For "Peter Steinberger", a WebSearch for `Peter Steinberger github profile site:github.com` returns @steipete. Pass `--github-user=steipete`.
- For "Matt Van Horn": `--github-user=mvanhorn`
- For "Garry Tan": `--github-user=garrytan`

**Person-mode GitHub tells a different story than keyword search.** Instead of "who mentioned this person in an issue body," it answers: "What are they shipping? Where are they getting merged? What do their own projects look like?" The engine fetches PR velocity, top repos with star counts, release notes, and README summaries.

**Skip this step if:**
- TOPIC is clearly NOT a person (products, concepts, events)
- TOPIC already has `--github-user` specified by the user
- Using `--quick` depth
- WebSearch shows no GitHub profile for this person (report "no GitHub handle found for this person" and proceed without `--github-user` rather than fabricating one)

Store: `RESOLVED_GITHUB_USER = {username or empty}`

**Checkpoint for person topics:** by the time you reach the Research Execution command, for a person topic you MUST have BOTH `RESOLVED_HANDLE` (from Step 0.5) AND `RESOLVED_GITHUB_USER` (from this step) OR an explicit "no X account" / "no GitHub profile" note. The Bash command that follows must include BOTH `--x-handle={handle}` AND `--github-user={handle}` when resolved. A person-topic run that shows only one of the two is a Step 0.5b regression.

### Step 0.5c: Resolve GitHub Repos (if topic is a product/project)

If TOPIC looks like a product, tool, or open source project (not a person), resolve its GitHub repo for project-mode search:

```
WebSearch("{TOPIC} github repo site:github.com")
```

From the results, extract `owner/repo` from URLs like `github.com/{owner}/{repo}`.

Pass to the CLI: `--github-repo={owner/repo}`

For comparisons ("X vs Y"), resolve repos for both topics: `--github-repo={repo_a},{repo_b}`

Example for "OpenClaw": `--github-repo=openclaw/openclaw`
Example for "OpenClaw vs Paperclip": `--github-repo=openclaw/openclaw,paperclipai/paperclip`

Project-mode GitHub fetches live star counts, README snippets, latest releases, and top issues directly from the API. This is always more accurate than blog posts or YouTube videos citing weeks-old numbers.

**Skip this step if:**
- TOPIC is a person (use `--github-user` instead)
- TOPIC has no GitHub presence (not a software project)
- WebSearch shows no GitHub repo for this topic

Store: `RESOLVED_GITHUB_REPOS = {comma-separated owner/repo or empty}`

### Step 0.5d: Resolve Trustpilot Domain (if topic is a company/brand)

When TOPIC is a company, brand, or service and you want Trustpilot review evidence, resolve its Trustpilot review-page domain. Trustpilot pages are keyed by domain (`www.thriftbooks.com`), not company name — a bare name 404s. Passing `--trustpilot-domain` (or a per-entity `trustpilot_domain` in `--competitors-plan`) auto-activates the opt-in Trustpilot source for that run — you do not also need `INCLUDE_SOURCES=trustpilot`.

**You usually already have it.** Step 0.55 item 6 (first-party positioning) fetches the official site — capture the bare hostname while you're there. When positioning wasn't fetched, one lookup covers it:

```
WebSearch("{TOPIC} official site")
```

Pass to the CLI: `--trustpilot-domain={domain}` (e.g., `--trustpilot-domain=www.thriftbooks.com`)

The flag is used verbatim, bypasses the engine's brand-shape gate, and auto-activates Trustpilot for the run, so it also unlocks Trustpilot for multi-word company names ("Stanley Steemer carpet cleaning"). For comparisons, put a per-entity `trustpilot_domain` in each PEER entity's `--competitors-plan` entry; the MAIN topic's domain must ride the outer `--trustpilot-domain` flag (the engine does not read a main-topic entry out of the plan).

**A miss is not fatal.** When the flag is absent, the engine resolves name → domain itself via the CLI's search **only when Trustpilot is already active** (`INCLUDE_SOURCES=trustpilot` or `--search` includes it); headless `--auto-resolve` fills a hint the engine verifies, but that hint alone does not activate the source. Resolve the flag when the domain is already in hand or the company name is ambiguous (lookalike or same-named companies) — an explicit domain is the only way to guarantee the right company *and* turn the source on.

**Skip this step if:**
- TOPIC is a person, event, or abstract concept (no company reviews to fetch)
- You intentionally want Trustpilot off for this run (`EXCLUDE_SOURCES=trustpilot`)

Store: `RESOLVED_TRUSTPILOT_DOMAIN = {domain or empty}`

---

### Step 0.5e: Decide the Amazon Buyer-Signal Lane (if `brightdata` is available)

**Availability first.** This lane exists only when the Bright Data CLI is on PATH and logged in (`--diagnose` reports `brightdata_installed` and `brightdata_authenticated`). If either is false the source does not exist, nothing changes, and you should skip this step entirely — do not mention it, do not suggest installing it mid-run.

**The one question to ask:** *would recent Amazon buyer sentiment materially inform this report?* Not "is this shopping" — the test is whether buyer evidence is real evidence for this topic.

| Topic | Fires? | `--amazon-query` |
|---|---|---|
| "Weber Grills" | Yes — brand topic where review signal is core evidence | `Weber grill` |
| "best bluetooth speaker under $100" | Yes — buying question, the whole point | `bluetooth speaker` |
| "Bentgo Box" | Yes — brand line | `Bentgo lunch box` |
| "Matt Van Horn" (CEO of June) | Yes — **and the keyword is the company's product, not the person** | `June Oven` |
| "Kanye West" | No — person/culture topic, buyer reviews are noise | — |
| "the 2026 election" | No — nothing to buy | — |

**Two mechanics that matter:**

1. **The keyword is yours to choose and is often not the topic.** Map person → company → product line using what you know plus what Step 0.55 surfaced. A "Matt Van Horn" run that searches Amazon for his name returns nothing; searching `June Oven` returns his company's product reviews, which is the actual signal.
2. **Phrase it as brand plus category, never bare brand.** A bare brand keyword lands on Amazon's ad-heavy page 1 and can miss the brand's own bestsellers — a live `Bentgo` search returned 57 competitor ads and missed the flagship, while `Bentgo lunch box` surfaced it. Say `Weber grill`, not `Weber`.

**`--search` is replace-not-add.** Passing `--search` narrows the run to exactly the sources listed, so include the full intended set: `--search reddit,x,youtube,amazon` — never a bare `--search amazon`, which would silently drop every other source.

**Cost and latency, so you can set expectations:** one credit for the product search plus one per review pull, 4 per typical run against a 5,000/month free tier. Review sampling adds roughly 30 seconds to 2 minutes at default depth. Quick depth pulls no reviews at all.

Store: `AMAZON_QUERY = {product keyword or empty}` — pass as `--amazon-query="{AMAZON_QUERY}"` and add `amazon` to `--search`.

**Skip this step if:** the CLI is unavailable, the topic has no consumer-product dimension, or the user set `EXCLUDE_SOURCES=amazon`.

---

### Step 0.5f: Decide the Meta Ads Lane (if a ScrapeCreators key is set)

**Availability first.** This lane exists only when `SCRAPECREATORS_API_KEY` is configured (`--diagnose` reports `has_scrapecreators`). Without it the source does not exist, nothing changes, and you should skip this step entirely — do not mention it, do not suggest signing up mid-run.

**The one question to ask:** *is there a brand here whose own paid message is evidence?* This lane answers "what is this company paying to say right now" — its live creatives, the products it is pushing, the promo codes it is running, and what its video ads say out loud. It is not a conversation source: nothing here is what people think about the brand, only what the brand is telling them.

| Topic | Fires? | Why |
|---|---|---|
| A consumer-brand topic | Yes — the brand's own campaign is first-party evidence | Paid message next to customer reaction |
| A retailer or membership warehouse | Yes — current promotions and seasonal push | Live offers are the story |
| A direct-to-consumer startup | Yes — positioning shows up in ad copy first | Often the earliest signal of a repositioning |
| A person, an executive, a creator | No — people do not run Ad Library campaigns | Their company might; use the company as the topic |
| An AI tool, a framework, a developer product | No — resolution returns unrelated advertisers | A live check on one such topic returned 1,467 wrong-entity ads |
| A news, politics, or culture topic | No — nothing to resolve | The lane ends unresolved and spends a credit finding that out |

**Three mechanics that matter:**

1. **Resolution can pick the wrong company, and the footer tells you when it did.** The lane resolves the advertiser page by name from an ad search. The 📣 footer line always names the page it resolved, and says `matched by partial name` when it fell back to the weakest match, so check it. If the advertiser is not the brand you meant, find the real page id and re-run with `--meta-ads-page`: `WebSearch("{TOPIC} facebook ad library")`, open the Ad Library result, and take the digits from its `view_all_page_id=` parameter. A `facebook.com/<name>` vanity URL is not a page id and the flag rejects it.
2. **A brand that advertises under product-line names still resolves.** Matching works in both directions, so an umbrella topic finds a product-named page and vice versa. What does not resolve is a brand whose pages share no word with the topic; that is the override's main use.
3. **The window means launched, not running.** Items are creatives that *started* inside the last 30 days. Long-running creatives from before are counted on the footer but never ranked, because "still advertising" is not news and "just launched this" is.

**`--search` is replace-not-add.** Passing `--search` narrows the run to exactly the sources listed, so include the full intended set: `--search reddit,x,youtube,meta_ads` — never a bare `--search meta_ads`, which would silently drop every other source.

**Cost and latency, so you can set expectations:** one or two credits to resolve the advertiser (a second only when the first search finds no name match), up to two more for its creatives, and up to three for video transcripts — at most seven per default-depth run against a 10,000-call free tier. Transcripts add roughly 15 to 45 seconds. Quick depth pulls no transcripts at all, though it still spends the resolve and one page.

Store: `META_ADS_PAGE = {page id or empty}` — add `meta_ads` to `--search`, and pass `--meta-ads-page="{META_ADS_PAGE}"` only when you have a page id.

**Skip this step if:** no ScrapeCreators key is set, the topic has no brand whose advertising is evidence, or the user set `EXCLUDE_SOURCES=meta_ads`.

---
