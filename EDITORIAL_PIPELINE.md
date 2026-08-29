# The editorial pipeline: multi-language collection, fact-checking, human approval

This is the part of the brief that matters most, so it's worth being precise
about what this system can and can't guarantee.

**No automated pipeline can promise a wrong fact will never be published.**
What this pipeline does instead is stack three independent safeguards, so
that an error has to slip past all three before it reaches your readers:

1. **Corroboration requirement** — a story is only drafted if it's reported
   by 2+ independent sources (different domains), or 1 official/government
   source plus 1 independent one. Single-source claims are logged and
   skipped, never drafted.
2. **Source-grounded drafting** — the drafting prompt explicitly instructs
   the model to use *only* facts present in the collected source snippets,
   and every article is generated with a visible, clickable source list.
3. **Human approval gate (the real backstop)** — every draft lands as a
   **pull request**, never a direct commit to `main`. GitHub Pages only ever
   builds from `main`. Until *you* click "Merge", the article does not
   exist on the live site, full stop — not "is hidden," but genuinely does
   not exist on the published site.

## How it works, end to end

1. `.github/workflows/editorial-pipeline.yml` runs on a schedule (every 6
   hours by default — change the cron expression to taste).
2. `scripts/draft_articles.py` reads `_data/sources.yml`, pulls recent items
   from each feed, and clusters items that look like the same story by
   title-keyword overlap across different source domains.
3. Clusters that clear the corroboration bar get sent to the Claude API with
   a strict prompt (see the script — it's short and worth reading) that
   forbids inventing facts, requires picking one of your 11 categories, and
   returns structured JSON.
4. The script writes a new file into `_posts/` with `pending_review: true`
   in its front matter and a `sources:` list built directly from the
   original URLs.
5. The workflow opens a pull request containing that new file (via the
   `peter-evans/create-pull-request` action), labelled `needs-review`, with
   a reviewer checklist in the PR description.
6. **You review it.** Read the article, click through the sources, confirm
   they say what the draft claims they say, edit anything wrong directly on
   the PR, then merge. Merging is what publishes it — GitHub Pages rebuilds
   the live site automatically within about a minute of the merge.

If a run finds nothing corroborated, no PR is opened — you won't get spammed
with empty pull requests.

## One-time setup (about 5 minutes)

1. **Get an Anthropic API key**: console.anthropic.com → Settings → API
   Keys → Create key. (This is a paid API, separate from any Claude
   subscription — drafting a handful of articles a day costs a small
   fraction of a dollar, but it's not literally free; keep an eye on usage
   in the console.)
2. In your GitHub repo: **Settings → Secrets and variables → Actions → New
   repository secret**. Name it `ANTHROPIC_API_KEY`, paste the key, save.
3. **Settings → Actions → General → Workflow permissions**: select "Read and
   write permissions" and check "Allow GitHub Actions to create and approve
   pull requests." (Without this, the pipeline can draft articles but can't
   open the PR for you to review.)
4. That's it. The workflow will run on its next scheduled tick, or trigger
   it immediately from the **Actions** tab → "KINETIX editorial pipeline" →
   "Run workflow".

## Improving source coverage over time

`_data/sources.yml` ships with a starter list across English, French,
German and Spanish outlets, plus an Indian government feed. Two things worth
doing in your first week:

- **Verify every feed URL actually resolves** (open each one in a browser —
  RSS paths change without notice) and swap out anything dead.
- **Add sources in more languages** relevant to the countries you want
  deeper coverage of — Russian, Mandarin, Japanese, Korean and Hebrew
  outlets would meaningfully widen the "world" in "world defence tech."
  The translation step already handles non-English input; it just needs
  feeds to read from.

## If you'd rather not run an LLM-driven pipeline at all

That's a completely reasonable choice — you can ignore
`.github/workflows/editorial-pipeline.yml` entirely (it does nothing without
the API key secret) and just write new posts by hand in `_posts/`, following
the front-matter format used by the 12 launch articles. The corroboration
and sourcing discipline described in `methodology/index.html` applies either
way — it's a standard for the writing, not a feature of the automation.
