# Updating your website (no coding)
This is file editing on GitHub, not a dashboard. A dashboard is a later phase.
Open a file, press the pencil, edit, then **Commit changes**. If something is wrong, the build stops and the live site stays as it was; read the error under **Actions**.

## Replace demo images with your work
Only use work you own and have permission to publish. The repository is public.
1. Open `site/static/media`, **Add file → Upload files**. Use simple names, e.g. `wedding-01.jpg`. Keep each under about 5 MB.
   The published copy is resized and location data removed, but the file you upload is publicly visible in the repository **as is**: export without GPS data.
2. In `content/portfolio.json`, replace one demo entry:

```json
{"slug": "traditional-marriage-eket", "title": "Your title", "category": "Traditional Marriages",
 "demo": false, "description": "Short description.", "location": "Eket", "date": "2026",
 "images": [{"file": "wedding-01.jpg", "alt": "Describe what the photo shows"}],
 "video": ""}
```
`slug` is lowercase with hyphens and unique. `category` must match the list at the top of the file.
For films, set `video` to the https *embed* link from your video host. Do not upload long films to GitHub.
Delete the remaining demo entries once you have real work.

## Packages and prices
In `content/packages.json`, add to `packages`:
`{"name": "...", "description": "...", "includes": ["..."], "price_ngn": null, "owner_approved": false}`
Only entries with `owner_approved: true` are shown. `price_ngn: null` shows "Let me confirm the exact quotation with Pete."
Enter only your latest approved prices (October Master Price Authority for frames). A public repository shows unapproved entries too.

## Testimonials
`content/testimonials.json`: `[{"name": "...", "quote": "...", "verified": true, "consent": true}]`

## Articles
`content/posts.json`: `[{"slug": "my-article", "title": "...", "summary": "...", "date": "2026-12-01", "body": ["Paragraph one.", "Paragraph two."], "published": true}]`

## Contacts, services, FAQ
`business.json`, `services.json`, `faq.json`.
