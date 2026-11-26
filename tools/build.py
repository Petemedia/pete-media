#!/usr/bin/env python3
"""Build the website: content/*.json + site/static -> dist/. Needs Python 3.9+; Pillow optional."""
import json, re, shutil, sys
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"
STATIC = ROOT / "site" / "static"

def load(name):
    return json.loads((ROOT / "content" / f"{name}.json").read_text(encoding="utf-8"))

B = load("business"); SERVICES = load("services"); PF = load("portfolio")
PACKS = load("packages"); TESTIMONIALS = load("testimonials"); POSTS = load("posts"); FAQ = load("faq")
e = lambda s: escape(str(s), quote=True)
ADDRESS = f'{B["street"]}, {B["city"]}, {B["region"]}, {B["country"]}'
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
pages = []

def wa(text="Hello Pete Media, I would like to make an enquiry."):
    return f'https://wa.me/{B["whatsapp"]}?text={quote(text)}'

def validate():
    errors, seen = [], set()
    for p in PF["projects"]:
        s = p.get("slug", "")
        if not SLUG.match(s) or s in seen: errors.append(f"bad or duplicate project slug: {s!r}")
        seen.add(s)
        if p.get("category") not in PF["categories"]: errors.append(f"{s}: unknown category")
        if not p.get("demo") and not (p.get("images") or p.get("video")):
            errors.append(f"{s}: a real project needs at least one image or a video")
        for im in p.get("images", []):
            if not im.get("alt"): errors.append(f"{s}: every image needs an 'alt' description")
            if not (STATIC / "media" / im["file"]).is_file(): errors.append(f"{s}: missing file media/{im['file']}")
        if p.get("video") and not (p["video"].startswith("https://") or (STATIC / "media" / p["video"]).is_file()):
            errors.append(f"{s}: video must be an https embed link or a file in media/")
    for t in TESTIMONIALS:
        if t.get("verified") and not t.get("consent"): errors.append("testimonial marked verified without consent")
    for p in POSTS:
        if not SLUG.match(p.get("slug", "")): errors.append("bad post slug")
    for p in PACKS["packages"]:
        if p.get("price_ngn") is not None and not p.get("owner_approved"):
            errors.append(f"package {p.get('name')}: has a price but owner_approved is not true")
    if errors:
        sys.exit("Content errors:\n- " + "\n- ".join(errors))

NAV = [("Work", "portfolio/"), ("Services", "services/"), ("Packages", "packages/"), ("About", "about/"), ("Contact", "contact/")]
MORE = [("Films", "films/"), ("Rental", "services/connectivity/"), ("Client delivery", "delivery/"), ("Insights", "blog/"), ("Testimonials", "testimonials/"), ("FAQ", "faq/")]

def page(path, title, desc, body, schema=None, index=True, image=None, root=None):
    """path is '' for home or 'a/b/'. Links are relative so the site works under any base path."""
    r = root if root is not None else "../" * path.count("/")
    url = B["site_url"] + path
    full = f"{title} | {B['name']}"
    link = lambda items: "".join(f'<a href="{r}{h}"{" aria-current=page" if h == path else ""}>{n}</a>' for n, h in items)
    ld = f'<script type="application/ld+json">{json.dumps(schema).replace("<", chr(92)+"u003c")}</script>' if schema else ""
    verify = f'<meta name="google-site-verification" content="{e(B["google_site_verification"])}">' if B["google_site_verification"] else ""
    og = f'<meta property="og:image" content="{e(B["site_url"] + image)}">' if image else ""
    robots = "" if index else '<meta name="robots" content="noindex">'
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(full)}</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0b0b0b">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website"><meta property="og:title" content="{e(full)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{e(url)}">{og}{verify}{robots}
<link rel="icon" href="{r}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{r}styles.css">{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="bar">
<a class="brand" href="{r or './'}">PETE MEDIA<small>FOTOGRAPHY</small></a>
<button class="menu" aria-expanded="false" aria-controls="nav" hidden>Menu</button>
<nav id="nav" aria-label="Main">{link(NAV)}<details><summary>More</summary><div>{link(MORE)}</div></details><a class="btn" href="{r}book/">Book</a></nav>
</header>
<main id="main">
{body}
</main>
<footer>
<div><strong>{e(B["name"])}</strong><p>{e(B["slogan"])}.</p></div>
<div><p>{e(ADDRESS)}<br>By appointment only. No walk-ins.</p></div>
<div><a href="{wa()}">WhatsApp {e(B["phone_primary"])}</a><a href="tel:+234{B["phone_secondary"].replace(" ", "")[1:]}">{e(B["phone_secondary"])}</a><a href="{e(B["instagram"])}">Instagram</a><a href="{e(B["facebook"])}">Facebook</a></div>
<div><a href="{r}privacy/">Privacy</a><a href="{r}terms/">Terms</a><p>&copy; {e(B["name"])}</p></div>
</footer>
<a class="float" href="{wa()}">WhatsApp</a>
<script src="{r}app.js" defer></script>
</body></html>
'''
    d = OUT / path
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.html").write_text(html, encoding="utf-8")
    if index: pages.append(url)

def head(eyebrow, h1, lead):
    return f'<section class="intro"><p class="eyebrow">{e(eyebrow)}</p><h1>{e(h1)}</h1><p class="lead">{e(lead)}</p></section>'

def cta(r, text="Planning something? Tell us the details."):
    return f'<section class="cta"><h2>{e(text)}</h2><p>No date is held without payment. A booking is confirmed only after payment is verified.</p><a class="btn" href="{r}book/">Book a consultation</a></section>'

def picture(r, p, im=None):
    if p.get("demo") or not (im or p.get("images")):
        label = "DEMO PLACEHOLDER" if p.get("demo") else "VIDEO"
        return f'<span class="ph">{label}<small>{e(p["category"])}</small></span>'
    im = im or p["images"][0]
    return f'<img src="{r}media/{e(quote(im["file"]))}" alt="{e(im["alt"])}" loading="lazy" decoding="async">'

def cards(r, projects):
    return '<div class="grid">' + "".join(
        f'<a class="card" data-cat="{e(p["category"])}" href="{r}portfolio/{p["slug"]}/">{picture(r, p)}<b>{e(p["title"])}</b></a>' for p in projects) + "</div>"

def service_cards(r):
    return '<div class="tiles">' + "".join(
        f'<a href="{r}services/{s["slug"]}/"><h3>{e(s["title"])}</h3><p>{e(s["short"])}</p></a>' for s in SERVICES) + "</div>"

def video(r, p):
    v = p.get("video")
    if not v: return ""
    if v.startswith("https://"):
        return f'<iframe class="video" src="{e(v)}" title="{e(p["title"])}" loading="lazy" allow="fullscreen; encrypted-media" allowfullscreen></iframe>'
    return f'<video class="video" controls preload="none" src="{r}media/{e(quote(v))}"></video>'

def build():
    validate()
    if OUT.exists(): shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    org = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": B["name"], "slogan": B["slogan"],
           "url": B["site_url"], "telephone": "+" + B["whatsapp"], "sameAs": [B["instagram"], B["facebook"]],
           "founder": {"@type": "Person", "name": B["founder"], "jobTitle": B["founder_title"]},
           "address": {"@type": "PostalAddress", "streetAddress": B["street"], "addressLocality": B["city"],
                       "addressRegion": B["region"], "addressCountry": B["country_code"]}}
    projects = PF["projects"]
    real = [p for p in projects if not p.get("demo")]
    demo_note = "" if real else '<p class="note">Approved Pete Media projects are being prepared. The tiles below are labelled placeholders, not client work.</p>'

    why = [("Clear terms", "You know what is quoted, what is paid and when a booking is confirmed."),
           ("One team, many needs", "Stills, film, live streaming and event internet can be planned together."),
           ("Appointment-based", "Time is set aside for you. Home service and agreed locations are available."),
           ("Privacy respected", "Client work is published only with permission.")]
    page("", "Photography, Films & Live Streaming in Eket, Akwa Ibom",
         "Premium photography, cinematic films, live streaming and creative media solutions from Pete Media Fotography in Eket, Akwa Ibom, Nigeria.",
         f'''<section class="hero"><p class="eyebrow">Eket &middot; Akwa Ibom &middot; Nigeria</p>
<h1>Beyond Moments.<br>Beyond Memories.<br><em>Beyond Ordinary.</em></h1>
<p class="lead">Premium photography, cinematic films, live-streaming and creative media solutions designed to preserve important moments and elevate brands.</p>
<p class="actions"><a class="btn" href="portfolio/">Explore our work</a><a class="btn ghost" href="book/">Book a consultation</a><a class="btn ghost" href="services/">Discover our services</a></p></section>
<section><h2>What we create</h2>{service_cards("")}</section>
<section><h2>Selected work</h2>{demo_note}{cards("", (real or projects)[:4])}<p><a class="more" href="portfolio/">View the portfolio</a> &middot; <a class="more" href="films/">Films and videos</a></p></section>
<section><h2>Why choose Pete Media</h2><div class="tiles">{"".join(f"<div><h3>{a}</h3><p>{b}</p></div>" for a, b in why)}</div></section>
<section><h2>Corporate and event solutions</h2><p class="lead">Coverage, broadcast and temporary connectivity for conferences, church programmes, launches and company events.</p><p><a class="more" href="services/corporate/">Business solutions</a></p></section>
{testimonial_block()}{cta("")}''', schema=org)

    page("about/", "About Pete Media", "About Pete Media Fotography and founder Emmanuel Denis Peter, based in Eket, Akwa Ibom.",
         head("About", B["slogan"] + ".", "Pete Media Fotography is a photography and visual media business in Eket, Akwa Ibom State, Nigeria.")
         + f'<section class="prose"><h2>{e(B["founder"])}</h2><p class="eyebrow">{e(B["founder_title"])}</p><p>Our standard rests on precision, creativity, trust, innovation and excellence.</p><p>We work by appointment. There are no walk-ins. Home service and agreed external locations are available.</p></section>' + cta("../"))

    page("services/", "Services", "Photography, videography, live streaming, corporate media and connectivity rental in Akwa Ibom.",
         head("Services", "Everything your story needs.", "Choose a service to see what it covers.") + f'<section>{service_cards("../")}</section>' + cta("../"))
    for s in SERVICES:
        page(f'services/{s["slug"]}/', f'{s["title"]} in Eket & Akwa Ibom', s["short"] + " Pete Media Fotography, Eket.",
             head("Services", s["title"], s["intro"]) + '<section><ul class="list">' + "".join(f"<li>{e(i)}</li>" for i in s["items"])
             + f'</ul><p><a class="btn ghost" href="{e(wa("Hello Pete Media, I would like a quotation for " + s["title"] + "."))}">Request a quotation on WhatsApp</a></p></section>' + cta("../../"),
             schema={"@context": "https://schema.org", "@type": "Service", "name": s["title"], "areaServed": "Akwa Ibom State", "provider": {"@type": "Organization", "name": B["name"]}})

    cats = [c for c in PF["categories"] if any(p["category"] == c for p in projects)]
    filters = '<div class="filters" hidden><button aria-pressed="true" data-filter="">All</button>' + "".join(f'<button aria-pressed="false" data-filter="{e(c)}">{e(c)}</button>' for c in cats) + "</div>"
    page("portfolio/", "Portfolio", "Photography and film portfolio of Pete Media Fotography.",
         head("Portfolio", "Selected work.", "Browse by category.") + f"<section>{demo_note}{filters}{cards('../', projects)}</section>" + cta("../"), index=bool(real))
    for p in projects:
        meta = " &middot; ".join(e(x) for x in (p["category"], p.get("location"), p.get("date")) if x)
        shots = "".join(f'<button class="shot" aria-label="View full screen">{picture("../../", p, im)}</button>' for im in p.get("images", []))
        page(f'portfolio/{p["slug"]}/', p["title"], p["description"] or p["title"],
             f'<section class="intro"><p class="eyebrow">{meta}</p><h1>{e(p["title"])}</h1><p class="lead">{e(p["description"])}</p></section><section>'
             + (video("../../", p) + f'<div class="grid">{shots}</div>' if not p.get("demo") else picture("../../", p))
             + '<p><button class="btn ghost share" hidden>Share this project</button></p></section><dialog class="viewer"><form method="dialog"><button>Close</button></form><img alt=""></dialog>' + cta("../../"),
             index=not p.get("demo"), image=("media/" + quote(p["images"][0]["file"])) if p.get("images") else None)

    films = [p for p in real if p.get("video")]
    page("films/", "Films and Videos", "Wedding films, event videos and corporate productions by Pete Media.",
         head("Films", "Stories in motion.", "Cinematic films and video productions.")
         + "<section>" + ("".join(f'<h2>{e(p["title"])}</h2>{video("../", p)}' for p in films) or '<p class="note">No approved films are published yet. Ask us on WhatsApp for current samples.</p>') + "</section>" + cta("../"), index=bool(films))

    approved = [p for p in PACKS["packages"] if p.get("owner_approved")]
    plist = "".join(
        f'<div><h3>{e(p["name"])}</h3><p>{e(p.get("description", ""))}</p><ul>' + "".join(f"<li>{e(i)}</li>" for i in p.get("includes", []))
        + "</ul><p><strong>" + (f'&#8358;{p["price_ngn"]:,}' if p.get("price_ngn") is not None else e(PACKS["fallback"])) + "</strong></p></div>" for p in approved)
    page("packages/", "Packages and Pricing", "Request a current Pete Media quotation for photography, video, streaming, framing and rental.",
         head("Packages", "Quoted to your event.", "Prices are in Nigerian naira and depend on scope, location and deliverables.")
         + "<section>" + (f'<div class="tiles">{plist}</div>' if plist else f'<p class="lead">{e(PACKS["fallback"])}</p><p>Send your requirements for a current quotation, including frames and enlargements.</p>') + "</section>" + cta("../"))

    def field(name, label, kind="text", req=False, extra=""):
        return f'<label>{label}{" *" if req else ""}<input name="{name}" data-label="{label}" type="{kind}" {"required" if req else ""} maxlength="120" {extra}></label>'
    def select(name, label, opts, req=False):
        return f'<label>{label}{" *" if req else ""}<select name="{name}" data-label="{label}" {"required" if req else ""}><option value="">Choose</option>' + "".join(f"<option>{e(o)}</option>" for o in opts) + "</select></label>"
    page("book/", "Book a Consultation", "Send a booking enquiry to Pete Media Fotography.",
         head("Bookings", "Tell us your plan.", "This form prepares a WhatsApp message for you to review and send. Nothing is stored on this website.")
         + f'''<section><div class="notice"><strong>This is an enquiry, not a booking.</strong> No date is held without payment. An advance or full payment is required, and a booking is confirmed only after payment is verified.</div>
<form id="booking" data-wa="{B["whatsapp"]}">
{field("name", "Your name", req=True, extra="autocomplete=name")}{field("phone", "Phone number", "tel", True, "autocomplete=tel")}{field("email", "Email address", "email", extra="autocomplete=email")}
{select("category", "Event category", ["Wedding", "Traditional marriage", "Pre-wedding", "Portrait", "Family", "Birthday or anniversary", "Church programme", "Funeral or memorial", "Corporate", "Commercial", "Framing or print", "Equipment rental", "Other"], True)}
{field("date", "Event date", "date", True)}{field("location", "Event location", req=True)}{field("start", "Start time", "time")}{field("end", "Expected finish time", "time")}{field("timezone", "Your time zone")}
{select("coverage", "Coverage", ["Photography", "Videography", "Photography and videography", "Not applicable"], True)}
{select("stream", "Live streaming", ["Yes", "No", "Not sure"])}{field("places", "Number of locations or coverage needs")}
{select("delivery", "Deliverables", ["Soft copies", "Printed products", "Both", "Not sure"])}{field("budget", "Budget range")}
{select("channel", "Preferred contact", ["WhatsApp", "Phone call", "Email"])}
<label class="wide">Special requests<textarea name="notes" data-label="Special requests" rows="4" maxlength="800"></textarea></label>
<label class="wide check"><input type="checkbox" required> I agree that these details are sent to Pete Media through WhatsApp to answer my enquiry (see <a href="../privacy/">Privacy</a>).</label>
<button class="btn wide" type="submit">Prepare WhatsApp enquiry</button>
</form><p id="sent" role="status"></p>
<noscript><p>Please enable JavaScript, or <a href="{wa()}">message us on WhatsApp</a>.</p></noscript></section>''')

    page("delivery/", "Client Delivery and File Retention", "How Pete Media delivers client media and how long digital files are kept.",
         head("Client delivery", "Your files, handled with care.", "Delivery arrangements are agreed with each client.")
         + '<section class="prose"><div class="notice"><strong>Digital client files are retained for three months.</strong> Download your files and keep your own backup within that period.</div><p>Online client accounts are not available on this website. For your delivery, contact us directly.</p>'
         + f'<p><a class="btn" href="{e(wa("Hello Pete Media, I am asking about the delivery of my files."))}">Ask about my files</a></p></section>')

    page("testimonials/", "Testimonials", "Verified client testimonials for Pete Media Fotography.",
         head("Testimonials", "Only real words.", "We publish feedback only with the client's permission.") + (testimonial_block() or '<section><p class="note">No testimonials are published yet.</p></section>') + cta("../"), index=bool(published_testimonials()))

    live = [p for p in POSTS if p.get("published")]
    page("blog/", "Insights", "Photography, events and media production notes from Pete Media.",
         head("Insights", "From behind the camera.", "Advice, stories and announcements.")
         + "<section>" + ("".join(f'<article><h2><a href="{p["slug"]}/">{e(p["title"])}</a></h2><p>{e(p["summary"])}</p></article>' for p in live) or '<p class="note">Articles are coming.</p>') + "</section>", index=bool(live))
    for p in live:
        page(f'blog/{p["slug"]}/', p["title"], p["summary"], f'<section class="intro"><p class="eyebrow">{e(p.get("date", ""))}</p><h1>{e(p["title"])}</h1></section><section class="prose">' + "".join(f"<p>{e(x)}</p>" for x in p["body"]) + "</section>")

    page("faq/", "Frequently Asked Questions", "Booking, payment, appointment and file retention questions.",
         head("FAQ", "Good to know.", "Short answers to common questions.") + '<section class="prose">' + "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in FAQ) + "</section>" + cta("../"))

    page("contact/", "Contact", "Contact Pete Media Fotography in Eket by WhatsApp or phone. Appointment only.",
         head("Contact", "Let's talk.", "By appointment only. Home service and agreed locations are available.")
         + f'<section class="prose"><p><a class="btn" href="{wa()}">WhatsApp {e(B["phone_primary"])}</a></p><p>Second line: {e(B["phone_secondary"])}</p><p>{e(ADDRESS)}</p><p><a href="{e(B["instagram"])}">Instagram</a> &middot; <a href="{e(B["facebook"])}">Facebook</a></p></section>' + cta("../"), schema=org)

    draft = '<div class="notice">Draft pending owner and legal review.</div>'
    page("privacy/", "Privacy Notice", "How Pete Media handles personal information.",
         head("Legal", "Privacy notice.", "What happens to your information.") + f'<section class="prose">{draft}<h2>This website</h2><p>It sets no cookies, runs no analytics and stores no form entries. The booking form builds a message on your device; it is sent only when you press send in WhatsApp, and WhatsApp\'s own terms then apply. The hosting provider may log technical data such as IP addresses. Embedded videos, when present, are served by their provider.</p><h2>Enquiries and bookings</h2><p>We use the details you send to answer you, quote, deliver the agreed work and keep necessary business records. Digital client files are retained for three months.</p><h2>Your rights</h2><p>Under the Nigeria Data Protection Act 2023 you may ask to access, correct or delete your personal data, or object to its use, and may complain to the Nigeria Data Protection Commission. Contact us on WhatsApp or at {e(ADDRESS)}.</p></section>', index=False)
    page("terms/", "Booking Terms", "Pete Media booking and payment terms.",
         head("Legal", "Booking terms.", "The essentials.") + f'<section class="prose">{draft}<ul><li>Work is by appointment. No walk-ins.</li><li>No date is held without payment.</li><li>An advance or full payment is required to validate a booking.</li><li>A booking is confirmed only after payment is verified.</li><li>Quotations, discounts, refunds and unusual requests are decided by the owner.</li><li>Digital client files are retained for three months.</li></ul></section>', index=False)

    page("404/", "Page not found", "Page not found.", head("404", "Page not found.", "Return to the home page.") + f'<section><a class="btn" href="{e(B["site_url"])}">Home</a></section>', index=False, root=B["site_url"])
    shutil.copy(OUT / "404" / "index.html", OUT / "404.html")
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{e(u)}</loc></url>" for u in pages) + "</urlset>\n")
    (OUT / "robots.txt").write_text(f'User-agent: *\nAllow: /\nSitemap: {B["site_url"]}sitemap.xml\n')
    optimise()
    print(f"Built {len(list(OUT.rglob('*.html')))} pages into dist/")

def published_testimonials():
    return [t for t in TESTIMONIALS if t.get("verified") and t.get("consent")]

def testimonial_block():
    t = published_testimonials()
    if not t: return ""
    return '<section><h2>Client words</h2><div class="tiles">' + "".join(f'<blockquote><p>{e(x["quote"])}</p><cite>{e(x["name"])}</cite></blockquote>' for x in t) + "</div></section>"

def optimise():
    """Resize large images and strip EXIF/GPS from the published copies. Originals are not touched."""
    files = [f for f in (OUT / "media").rglob("*") if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not files: return
    try:
        from PIL import Image, ImageOps
    except ImportError:
        sys.exit("Install Pillow to build with photographs: pip install Pillow")
    for f in files:
        with Image.open(f) as im:
            out = ImageOps.exif_transpose(im)
            out.thumbnail((2000, 2000))
            clean = Image.frombytes(out.mode, out.size, out.tobytes()) if out.mode != "P" else out.convert("RGBA")
        clean.save(f, quality=82, optimize=True)

if __name__ == "__main__":
    build()
