# pete-media
Official website of Pete Media Fotography — Creating Top-Notch Memories.

    python3 tools/build.py          # builds dist/
    python3 tests/check_site.py     # link, heading, alt and secret checks
    python3 tests/browser_test.py   # needs playwright
    bash tests/run_db_tests.sh      # needs local PostgreSQL

| Path | What |
|---|---|
| content/ | Text, services, portfolio, packages, testimonials, posts |
| site/static/ | Styles, script, media |
| tools/build.py | Page templates and generator |
| supabase/ | Database schema and rule tests |
| docs/ | Audit, guides, architecture, readiness |

Start with docs/GO-LIVE.md. The old index.html and style.css stay in place until the new site is live.
**This repository is public: never add client files, private prices or keys.**
