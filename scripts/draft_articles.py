#!/usr/bin/env python3
"""
KINETIX editorial pipeline — collection, corroboration & drafting stage.

What this script does:
  1. Reads the multi-language source list in _data/sources.yml
  2. Pulls recent items from each RSS/Atom feed
  3. Clusters items that look like the same underlying story (title-keyword
     overlap) across DIFFERENT source domains
  4. Only drafts an article for a cluster that clears the corroboration bar:
       - 2+ independent (different-domain) sources reporting the same thing, OR
       - 1 "official" source (see _data/sources.yml) + 1 independent source
  5. Calls the Anthropic API to draft a Jekyll-formatted article strictly
     from the supplied source snippets (the prompt explicitly forbids adding
     facts not present in the snippets)
  6. Writes the draft into _posts/ with `pending_review: true` in its front
     matter, on a NEW BRANCH — it never touches `main` directly.

What this script deliberately does NOT do:
  - It never merges, and never pushes to main. Publication only happens when
    a human merges the pull request this run's workflow opens. That gate is
    enforced by GitHub branch protection + the peter-evans/create-pull-request
    action in .github/workflows/editorial-pipeline.yml, not by this script,
    so a bug here can't accidentally publish something.
  - It never claims a single-source story is verified. If corroboration
    fails, the item is logged and skipped, not drafted.

Requires the ANTHROPIC_API_KEY secret (see EDITORIAL_PIPELINE.md for setup).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlparse

import feedparser
import yaml
from dateutil import parser as dtparser

ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = ROOT / "_data" / "sources.yml"
CATEGORIES_FILE = ROOT / "_data" / "categories.yml"
POSTS_DIR = ROOT / "_posts"
LOG_FILE = ROOT / "scripts" / "seen_entries.json"

LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "36"))
MIN_TITLE_OVERLAP = 0.45  # Jaccard similarity threshold to consider two items the "same story"
MODEL = os.environ.get("KINETIX_MODEL", "claude-opus-4-5")

STOPWORDS = {
    "the", "a", "an", "of", "in", "on", "for", "to", "and", "with", "at",
    "by", "is", "as", "new", "news", "its", "into", "over", "after", "amid",
}


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_title(title):
    words = re.findall(r"[a-zA-Z0-9]+", title.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def domain_of(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return url


def load_seen():
    if LOG_FILE.exists():
        return set(json.loads(LOG_FILE.read_text()))
    return set()


def save_seen(seen):
    LOG_FILE.write_text(json.dumps(sorted(seen), indent=2))


def collect_entries(sources):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    entries = []
    for src in sources:
        try:
            feed = feedparser.parse(src["url"])
        except Exception as e:
            print(f"[warn] could not parse {src['name']}: {e}", file=sys.stderr)
            continue
        for e in feed.entries:
            pub = e.get("published") or e.get("updated")
            try:
                pub_dt = dtparser.parse(pub) if pub else None
            except Exception:
                pub_dt = None
            if pub_dt and pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            if pub_dt and pub_dt < cutoff:
                continue
            link = e.get("link", "")
            entries.append({
                "title": e.get("title", "").strip(),
                "link": link,
                "domain": domain_of(link),
                "source_name": src["name"],
                "lang": src.get("lang", "en"),
                "official": bool(src.get("official", False)),
                "summary": re.sub("<[^<]+?>", "", e.get("summary", ""))[:600],
                "published": pub_dt.isoformat() if pub_dt else None,
            })
    return entries


def cluster_entries(entries):
    """Greedy clustering by title-keyword overlap. Good enough for a first
    corroboration pass; a human editor is the real accuracy backstop."""
    clusters = []
    used = [False] * len(entries)
    keysets = [normalize_title(e["title"]) for e in entries]

    for i, e in enumerate(entries):
        if used[i]:
            continue
        cluster = [e]
        used[i] = True
        for j in range(i + 1, len(entries)):
            if used[j]:
                continue
            if jaccard(keysets[i], keysets[j]) >= MIN_TITLE_OVERLAP:
                cluster.append(entries[j])
                used[j] = True
        clusters.append(cluster)
    return clusters


def passes_corroboration(cluster):
    domains = {item["domain"] for item in cluster}
    has_official = any(item["official"] for item in cluster)
    if has_official and len(domains) >= 2:
        return True
    return len(domains) >= 2


def draft_prompt(cluster, categories):
    cat_list = "\n".join(f"- {c['slug']}: {c['name']} — {c['blurb']}" for c in categories)
    sources_block = "\n\n".join(
        f"SOURCE ({item['source_name']}, {item['domain']}, lang={item['lang']}):\n"
        f"Title: {item['title']}\nURL: {item['link']}\nSnippet: {item['summary']}"
        for item in cluster
    )
    return f"""You are drafting a news article for KINETIX, an independent defence-technology
publication. Follow these rules exactly:

1. Use ONLY the facts present in the SOURCE blocks below. Do not add any
   claim, figure, date, or capability that is not directly supported by at
   least one of these snippets. If a snippet is ambiguous or too thin to
   support a clear sentence, leave it out rather than guessing.
2. If sources are in a language other than English, translate the relevant
   facts into English yourself, but do not alter their meaning.
3. Pick exactly ONE category slug from this list that best fits the story:
{cat_list}
4. Write in a measured, factual, journalistic tone. No hype, no unearned
   superlatives, no speculation presented as fact.
5. Output STRICT JSON with this shape (no markdown fences, no commentary):
{{
  "title": "...",
  "category_slug": "...",
  "read_time": "N min read",
  "body_markdown": "## Optional subhead\\n\\nArticle body in Markdown, 300-600 words...",
  "corroboration_note": "One sentence on how the claims here were cross-checked across the sources below."
}}

SOURCES:
{sources_block}
"""


def call_claude(prompt):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")
    return json.loads(text)


def slugify(title):
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s[:70].rstrip("-")


def write_post(draft, cluster):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = slugify(draft["title"])
    filename = POSTS_DIR / f"{today}-{slug}.md"

    sources_yaml = "\n".join(
        f'  - label: "{item["source_name"]} — {item["title"]}"\n    url: {item["link"]}'
        for item in cluster
    )

    front_matter = f"""---
title: "{draft['title'].replace('"', "'")}"
date: {today} 09:00:00 +0530
categories: [{draft['category_slug']}]
author: KINETIX Editorial Desk
read_time: {draft.get('read_time', '4 min read')}
verified: true
pending_review: true
sources:
{sources_yaml}
corroboration: "{draft['corroboration_note'].replace('"', "'")}"
---
"""
    filename.write_text(front_matter + "\n" + draft["body_markdown"] + "\n", encoding="utf-8")
    return filename


def main():
    sources = load_yaml(SOURCES_FILE)
    categories = load_yaml(CATEGORIES_FILE)
    seen = load_seen()

    entries = collect_entries(sources)
    new_entries = [e for e in entries if e["link"] and e["link"] not in seen]
    print(f"Collected {len(entries)} entries, {len(new_entries)} unseen.")

    clusters = cluster_entries(new_entries)
    written = []

    for cluster in clusters:
        if not passes_corroboration(cluster):
            continue
        if "ANTHROPIC_API_KEY" not in os.environ:
            print("[error] ANTHROPIC_API_KEY not set — cannot draft. "
                  "See EDITORIAL_PIPELINE.md.", file=sys.stderr)
            sys.exit(1)
        try:
            draft = call_claude(draft_prompt(cluster, categories))
            path = write_post(draft, cluster)
            written.append(str(path.relative_to(ROOT)))
            print(f"Drafted: {path.name}")
        except Exception as e:
            print(f"[warn] failed to draft cluster ({cluster[0]['title']}): {e}", file=sys.stderr)

    for e in new_entries:
        seen.add(e["link"])
    save_seen(seen)

    # Emit a summary for the workflow / PR body.
    summary_path = ROOT / "scripts" / "last_run_summary.json"
    summary_path.write_text(json.dumps({
        "run_at": datetime.now(timezone.utc).isoformat(),
        "entries_scanned": len(entries),
        "new_entries": len(new_entries),
        "clusters_found": len(clusters),
        "articles_drafted": written,
    }, indent=2))

    if not written:
        print("No new corroborated stories this run — nothing drafted.")


if __name__ == "__main__":
    main()
