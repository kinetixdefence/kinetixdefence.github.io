# KINETIX — Global Defence Technology Intelligence

A Jekyll static site, built to deploy free on GitHub Pages, covering defence
technology across 11 categories with a source-cited, human-approved editorial
pipeline. This README is the deployment guide — start to finish.

---

## 1. What's in this repo

```
_config.yml            Site settings (title, plugins, permalinks)
_data/categories.yml    The 11 coverage categories
_data/sources.yml       Starter list of news sources for the auto-drafting pipeline
_layouts/               Page templates (default, article, category)
_includes/               Header, footer, article-card partials
_posts/                  12 launch articles, already written and cited
categories/<slug>/       The 11 category hub pages
about/, methodology/, submit-a-tip/, corrections/, privacy/, terms/, subscribe/, archive/
assets/css/style.css    All site styling (single file, no framework)
assets/img/             Logo + social-card SVGs
.github/workflows/editorial-pipeline.yml   The automated drafting pipeline (see EDITORIAL_PIPELINE.md)
scripts/draft_articles.py                  What that pipeline runs
GROWTH_PLAN.md          A realistic 10-day promotion plan
EDITORIAL_PIPELINE.md   How the fact-checking / approval pipeline works and how to turn it on
```

## 2. Deploy to GitHub Pages (free, ~10 minutes)

1. Create a free GitHub account if you don't have one, at github.com.
2. Create a **new public repository**. Name it whatever you like — for a
   *user site* (`https://<username>.github.io`) name it exactly
   `<your-username>.github.io`; for a *project site*
   (`https://<username>.github.io/kinetix`) any name works, e.g. `kinetix`.
3. Upload every file in this folder to that repository, preserving the
   folder structure exactly. Easiest way: install [GitHub Desktop](https://desktop.github.com/),
   clone your new empty repo, copy all these files into the cloned folder,
   then commit and push. (Command-line equivalent: `git init`, `git remote
   add origin <your repo URL>`, `git add .`, `git commit -m "Launch KINETIX"`,
   `git push -u origin main`.)
4. In your repository on GitHub: **Settings → Pages**. Under "Build and
   deployment", set Source to **"Deploy from a branch"**, branch **main**,
   folder **/(root)**. Save.
5. Wait 1-2 minutes, then refresh that page — GitHub will show you the live
   URL (either `https://<username>.github.io` or
   `https://<username>.github.io/<repo-name>`).
6. **If you used a project-site repo name** (not `<username>.github.io`),
   open `_config.yml` and set `baseurl: "/<repo-name>"` (matching your repo
   name exactly, with the leading slash), then commit that change — otherwise
   internal links will point to the wrong path.

That's it — no build step, no server, no cost. GitHub rebuilds the site
automatically every time you push a change to `main`.

## 3. Point a custom domain at it (optional, still free)

You don't need a custom domain to launch — the `github.io` URL works
immediately and is fine for early traffic and even AdSense once you're
eligible. If you want `www.yourdomain.com` later:
1. Buy a domain from any registrar (this costs money — GitHub Pages hosting
   itself stays free).
2. In the registrar's DNS settings, add a CNAME record pointing to
   `<username>.github.io`.
3. In your repo, add a file named `CNAME` (no extension) containing just
   your domain, e.g. `kinetixdefence.com`. Repo Settings → Pages will also
   let you enter this directly and it creates the file for you.

## 4. Before you tell anyone the URL, replace these placeholders

Search the repo for `kinetixdefence.example` and `@kinetixdefence` and replace
with real inboxes / handles:
- `submit-a-tip/index.html`, `corrections/index.html`, `privacy/index.html`,
  `terms/index.html` — placeholder email addresses.
- `_config.yml` — set `url:` to your actual GitHub Pages or custom-domain URL
  (this matters for the sitemap and RSS feed to work correctly).
- `subscribe/index.html` — currently a placeholder; the fastest free option
  is [Buttondown](https://buttondown.email) (free under 100 subscribers) —
  create an account, grab their embed form snippet, paste it into this page.

## 5. AdSense — what to expect, honestly

Google AdSense will not approve a brand-new site with mostly placeholder
policy pages and a few days of traffic. In practice you'll typically need:
original content accumulated over some weeks, a genuine and complete privacy
policy (replace the placeholder above with real specifics once you've
chosen an analytics/email tool), some organic traffic history, and no policy
violations. Apply once the site has a few weeks of real articles and
traffic — applying too early can result in a rejection that's slightly
harder to overturn than a first application. In the meantime, alternatives
that approve faster or don't gate on traffic history include affiliate
links to defence-industry publications/events, or a "support us" /
sponsorship page for direct advertiser outreach (relevant given your
audience — defence contractors, event organisers, and trade publications
are plausible direct advertisers even before AdSense is viable).

## 6. Turning on the automated editorial pipeline

The site works today with its 12 hand-written, sourced launch articles.
The `.github/workflows/editorial-pipeline.yml` automation that continuously
collects, fact-checks and drafts *new* articles for your approval is
optional and off by default (it simply won't run without an API key — see
**EDITORIAL_PIPELINE.md** for what it does and the 5-minute setup).

## 7. Local preview (optional)

If you have Ruby installed: `bundle install` then `bundle exec jekyll
serve`, then open `http://localhost:4000`. Not required for deployment —
GitHub Pages builds the site for you.
