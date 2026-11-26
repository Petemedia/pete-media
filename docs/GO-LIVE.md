# Going live
Do these in order. Your current site stays unchanged until step 2.
1. On GitHub: repository **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. Merge the pull request for branch `platform-v1`.
3. Open **Actions → Site** and wait for green ticks. Check the site on your phone.
4. After you are satisfied, the old `index.html` and `style.css` at the top level can be deleted.

Rollback: set the Pages source back to "Deploy from a branch" (main, root) while the old files are still there.
Custom domain: add it in Settings → Pages, then change `site_url` in content/business.json.

## Google
- Search Console: add a URL-prefix property, paste the verification code into `google_site_verification`, submit `sitemap.xml`.
  On a github.io project address, robots.txt is not read from the domain root; submit the sitemap directly.
- Business Profile (business.google.com): same name, phone and website. Appointment-only businesses can set up as a service-area business.
- Analytics is deliberately not installed. If added, update the privacy notice and consent first.
