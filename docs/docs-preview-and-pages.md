---
layout: default
title: Docs Preview and GitHub Pages
description: Preview the docs locally and publish to GitHub Pages.
prev_url: /troubleshooting.html
prev_title: Troubleshooting
next_url: /index.html
next_title: Documentation Overview
---

# Docs Preview and GitHub Pages

This page explains how to validate the docs UI locally before publishing and how to configure GitHub Pages correctly.

## Quick local preview in editor

For fast content checks:

1. Open any file in `docs/`
2. Use Markdown preview in your editor
3. Verify headings, links, and code blocks

This method is fast, but it does not fully reproduce layout behavior from Jekyll templates.

## Full local preview with Jekyll and Docker

From repository root:

```powershell
docker run --rm -it -p 4000:4000 -v "${PWD}:/srv/jekyll" jekyll/jekyll:pages jekyll serve --source /srv/jekyll/docs --destination /srv/jekyll/docs/_site --watch --force_polling
```

Then open:

```text
http://localhost:4000
```

This gives a near-production preview of:

- global layout
- sidebar and top navigation
- dark mode toggle
- generated table of contents
- previous/next links

## GitHub Pages publishing setup

In repository settings:

1. Open **Settings -> Pages**
2. Source: **Deploy from a branch**
3. Branch: **main**
4. Folder: **/docs**
5. Save

Expected site URL pattern:

```text
https://<username>.github.io/<repository>/
```

For this repository:

```text
https://shanen28.github.io/license-guard/
```

## Common Pages issues

### Site not updating

- Wait for the Pages workflow to complete
- Check GitHub Actions logs for build failures
- Ensure files are committed in `docs/` on `main`

### Missing styles or scripts

- Verify paths are relative (`{{ '/assets/...' | relative_url }}`)
- Ensure `docs/assets/...` files exist in the branch

### 404 on page links

- Use `.html` links in navigation for static pages
- Confirm page filenames match link targets
