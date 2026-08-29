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
