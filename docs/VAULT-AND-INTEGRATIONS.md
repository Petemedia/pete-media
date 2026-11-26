# Vault, backups and integrations (design only — none of this is built)

## Storage options (published list prices seen November 2026; verify before buying)
| Provider | Free | Paid | Downloads |
|---|---|---|---|
| Supabase Storage | 1 GB, 50 MB per file, 5 GB egress; project pauses after a week idle | Pro from $25/month with 100 GB | 250 GB on Pro |
| Cloudflare R2 | 10 GB | $0.015/GB-month | no egress fee (request fees apply) |
| Backblaze B2 | 10 GB | $6.95/TB-month | free up to 3x stored, then $0.01/GB |
Sources: https://supabase.com/pricing · https://developers.cloudflare.com/r2/pricing · https://www.backblaze.com/cloud-storage/pricing

## Estimate (assumption, replace with your figures)
At 200 GB of new media per month kept 3 months, about 600 GB is live: roughly $9/month on R2, $4/month on B2, before tax, request and exchange charges. Free tiers are not enough for photo and video delivery.
Suggestion: Supabase for accounts and database, R2 for client delivery, B2 for the independent backup.

## Vault design
Private buckets only; paths `client/project/{originals,edited,previews,delivery}/`; short-lived signed links issued by a server after a permission check; multipart uploads; per-file checksum and size recorded; expiry at three months with notice before deletion (confirm whether this applies to originals).

## Backups
Three copies, two media types, one off-site. Today: PM-INFINITY scripts (INSTALL_PM_INFINITY.ps1; not tested in this audit) to a second drive, plus a cloud copy later. Test a restore monthly. Database: Supabase free has no automatic backups to rely on; export with pg_dump or use Pro.

## What each integration needs from you
| Integration | Needed |
|---|---|
| WhatsApp assistant | Meta business verification, WhatsApp Business Platform number or provider, message templates, server, AI API key; message and AI usage fees. Check what happens to the existing app on the number before moving it |
| Google Calendar | Google Cloud project, OAuth consent, authorisation by the calendar owner, server worker to process calendar_events |
| Reminders and notices | Email/SMS/WhatsApp provider and a scheduler |
| Online payments | Merchant account (for example Paystack or Flutterwave) and signed webhook verification |
| Client portal and dashboard | Supabase project, hosting for the app |

Assistant rules for the future build: never invent price or availability; never confirm, discount or refund; quote only approved settings; otherwise say "Let me confirm the exact quotation with Pete." and escalate.
