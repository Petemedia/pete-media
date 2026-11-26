# Technical audit (26 November 2026)

## Found
- Public repository, 5 files, GitHub Pages enabled. One `index.html` and `style.css`; no build, tests, backend or dependencies.
- `index.html` points to `assets/photos/*` and `assets/videos/showreel.mp4`; none are in the repository.
- Editing notes ("YOUR SIGNATURE IMAGE", "Replace every sample tile") are visible to visitors.
- The first version (commit 87aee58) used Unsplash stock photography.
- No sitemap, canonical URL, structured data, privacy notice or terms.
- No secrets seen in the current files (full secret-history scan not performed).
- The live URL could not be opened from the build environment, so live behaviour is inferred from the files.

## Preserved
Contact numbers, social links, address, appointment-only and booking wording, black-and-gold identity,
the launch notes (README-FIRST.md) and the PM-INFINITY local archive installer.

## To confirm with the owner
- Instagram @pete_media and Facebook /petemedia.ng are the correct accounts.
- Every listed service is currently operational (list is in content/services.json). Future digital services are not advertised.

## Roadmap
| Phase | Status |
|---|---|
| 1 Inspection | Done |
| 2 Website | Built; needs real photographs, logo, approval |
| 3 Business functions | Database rules built and tested locally. No dashboard or API yet |
| 4 Client accounts and galleries | Not built |
| 5 Vault | Design only (VAULT-AND-INTEGRATIONS.md) |
| 6 WhatsApp, Calendar, AI | Not built; needs accounts and approvals |
| 7 International | Time zone captured, currency columns exist. English only, no online payments |
| 8 Testing and deployment | Site and database rules tested; not deployed |
