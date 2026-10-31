#!/usr/bin/env python3
"""Builds index.html, cv.html, downloads/cv-academic.md, downloads/publications.bib and sitemap.xml
from data/cv.public.json.

Usage (from the site root):  python3 tools/build.py
Standard library only. Publishing does not require running this script:
the generated files are committed together with the JSON.
"""
import json
import re
import unicodedata
from collections import OrderedDict
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "cv.public.json").read_text(encoding="utf-8"))
P = DATA["person"]
SITE = DATA["meta"].get("site_url")

MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]


def long_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    return f"{d} {MONTHS[m - 1]} {y}"


def e(s):
    return escape(str(s), quote=True) if s is not None else ""


# ------------------------------------------------------------------ authors (IEEE)
PARTICLES = {"de", "del", "la", "las", "los", "y", "da", "do", "dos", "van", "von"}


def initials(given):
    out = []
    for tok in re.split(r"\s+", given.replace(".", ". ").strip()):
        if not tok:
            continue
        if tok.lower() in PARTICLES:
            out.append(tok.lower())
        elif "-" in tok:
            out.append("-".join(t[0] + "." for t in tok.split("-") if t))
        else:
            out.append(tok[0] + ".")
    return " ".join(out)


def ieee_name(a):
    return f"{initials(a.get('given', ''))} {a['family']}".strip()


def join_names(names):
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + ", and " + names[-1]


def authors_html(lst):
    return join_names([f"<strong>{e(ieee_name(a))}</strong>" if a.get("me") else e(ieee_name(a)) for a in lst])


def authors_md(lst):
    return join_names([f"**{ieee_name(a)}**" if a.get("me") else ieee_name(a) for a in lst])


TYPE_LABEL = OrderedDict([
    ("article", "Journal articles"),
    ("book", "Edited book"),
    ("chapter", "Book chapters (international publishers)"),
    ("proceedings", "Conference papers"),
    ("preprint", "Preprints"),
    ("other", "Other articles (outreach and non-indexed venues)"),
    ("chapter_inst", "Chapters in UABC edited volumes"),
])


def ref_parts(p, fmt="html"):
    """IEEE reference as HTML or Markdown."""
    H = fmt == "html"
    it = (lambda s: f"<i>{e(s)}</i>") if H else (lambda s: f"*{s}*")
    tx = e if H else (lambda s: str(s))
    au = authors_html(p["authors"]) if H else authors_md(p["authors"])
    eds = authors_html(p.get("editors") or []) if H else authors_md(p.get("editors") or [])
    neds = len(p.get("editors") or [])
    t = p["type"]
    bits = []
    if t == "book":
        bits.append(f"{eds}, {'Eds.' if neds > 1 else 'Ed.'}, {it(p['title'])}. {tx(p['publisher'])}, {p['year']}")
        if p.get("isbn"):
            bits.append(f"ISBN {tx(p['isbn'])}")
    else:
        head = f"{au}, “{tx(p['title'])},”"
        if t == "chapter":
            s = f"{head} in {it(p['venue'])}"
            s += f", {eds}, {'Eds.' if neds > 1 else 'Ed.'}" if neds else "."
            if p.get("series"):
                s += f" (ser. {tx(p['series'])})."
            s += f" {tx(p['publisher'])}, {p['year']}"
            bits.append(s)
            if p.get("pages"):
                bits.append(f"pp. {tx(p['pages'])}")
        elif t == "chapter_inst":
            bits.append(f"{head} ch. {tx(p['chapter'])} in an edited volume. Universidad Autónoma de Baja California, {p['year']}")
            bits.append(f"ISBN {tx(p['isbn'])}")
        elif t == "proceedings":
            bits.append(f"{head} in {it(p['venue'])}, {p['year']}")
            if p.get("pages"):
                bits.append(f"pp. {tx(p['pages'])}")
        elif t == "preprint":
            bits.append(f"{head} {it(p['venue'])}, {p['year']}")
        else:
            bits.append(f"{head} {it(p['venue'])}")
            if p.get("volume"):
                bits.append(f"vol. {tx(p['volume'])}")
            if p.get("issue"):
                bits.append(f"no. {tx(p['issue'])}")
            if p.get("article_number"):
                bits.append(f"Art. no. {tx(p['article_number'])}")
            elif p.get("pages"):
                bits.append(f"pp. {tx(p['pages'])}")
            bits.append(str(p["year"]))
    ref = ", ".join(bits)
    if p.get("doi"):
        url = "https://doi.org/" + p["doi"]
        ref += f", doi: <a href=\"{e(url)}\">{e(p['doi'])}</a>." if H else f", doi: [{p['doi']}]({url})."
    elif p.get("url"):
        ref += (f". [Online]. Available: <a href=\"{e(p['url'])}\">{e(p['url'])}</a>" if H
                else f". [Online]. Available: <{p['url']}>")
    else:
        ref += "."
    return ref


PUBS = sorted(DATA["publications"], key=lambda p: (-(p["year"] or 0), p["title"].lower()))
BY_ID = {p["id"]: p for p in PUBS}
COUNT = {t: sum(1 for p in PUBS if p["type"] == t) for t in TYPE_LABEL}
THESES = DATA["theses"]
LEVELS = ("Ph.D.", "M.Sc.", "B.Sc.")
TH_COUNT = {lvl: sum(1 for t in THESES if t["level"] == lvl) for lvl in LEVELS}
UPDATED = long_date(DATA["meta"]["updated"])
M = DATA["metrics"]
PHOTO = P.get("photo")

# ------------------------------------------------------------------ shared pieces
HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{name}">
{canonical}<meta property="og:type" content="profile">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="en_US">
{ogimage}<meta name="color-scheme" content="light">
<link rel="stylesheet" href="assets/css/styles.css">
{extra}</head>
"""


def head(title, desc, page, extra=""):
    canonical = f'<link rel="canonical" href="{e(SITE + page)}">\n<meta property="og:url" content="{e(SITE + page)}">\n' if SITE else ""
    ogimage = f'<meta property="og:image" content="{e(SITE + PHOTO["src"])}">\n<meta property="og:image:alt" content="{e(PHOTO["alt"])}">\n' if (SITE and PHOTO) else ""
    return HEAD.format(title=e(title), desc=e(desc), name=e(P["name"]), canonical=canonical, ogimage=ogimage, extra=extra)


def portrait(cls):
    if not PHOTO:
        return ""
    return (f'<img class="{cls}" src="{e(PHOTO["src"])}" alt="{e(PHOTO["alt"])}" '
            f'width="{PHOTO["width"]}" height="{PHOTO["height"]}" decoding="async">')


def header(active):
    nav = [("index.html", "Home"), ("cv.html", "Full CV"), ("cv.html#publications", "Publications"),
           ("cv.html#contact", "Contact")]
    cur = ' aria-current="page"'
    items = "".join(f'<li><a href="{h}"{cur if h == active else ""}>{t}</a></li>' for h, t in nav)
    return f"""<a class="skip-link" href="#content">Skip to content</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="brand" href="index.html"><span class="brand-name">{e(P['name'])}</span><span class="brand-sub">FIAD · UABC</span></a>
    <nav aria-label="Main"><ul class="main-nav">{items}</ul></nav>
  </div>
</header>
"""


def footer():
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p>{e(P['honorific'])} {e(P['name'])} · {e(P['unit'])}, {e(P['institution'])} · {e(P['location'])}</p>
    <p>Content updated on {UPDATED}. Sources: Mexican researcher CV (CVU, SECIHTI; cut-off 16 August 2026), public ORCID record and Crossref metadata.</p>
  </div>
</footer>
<script src="assets/js/main.js" defer></script>
</body>
</html>
"""


def id_links(cls="id-links"):
    out = [f'<li><a href="{e(l["url"])}" rel="me noopener">{e(l["label"])}</a></li>' for l in P["links"]]
    out.append(f'<li><a href="mailto:{e(P["email"])}">{e(P["email"])}</a></li>')
    return f'<ul class="{cls}">' + "".join(out) + "</ul>"


def metrics_block():
    return f"""<div class="metrics" role="group" aria-labelledby="metrics-title">
  <p id="metrics-title" class="metrics-title">Citation metrics</p>
  <dl class="metrics-grid">
    <div><dt>Citations</dt><dd>{M['citations']:,}</dd></div>
    <div><dt>h-index</dt><dd>{M['h_index']}</dd></div>
    <div><dt>i10-index</dt><dd>{M['i10_index']}</dd></div>
  </dl>
  <p class="metrics-note">Source: <a href="{e(M['url'])}">{e(M['source'])}</a>, accessed {long_date(M['retrieved'])}. {e(M['note'])}</p>
</div>"""


def stats_block():
    rows = [
        (COUNT["article"], "peer-reviewed journal articles"),
        (COUNT["book"], "edited book (CRC Press)"),
        (COUNT["chapter"], "book chapters (Springer, CRC Press)"),
        (len(DATA["ip"]["patents"]), "patents granted (IMPI, Mexico)"),
        (len(DATA["ip"]["software"]), "software copyright registrations"),
        (len(THESES), "theses supervised or co-supervised"),
    ]
    lis = "".join(f'<li><span class="stat-n">{n}</span> <span class="stat-l">{e(l)}</span></li>' for n, l in rows)
    return f'<ul class="stats">{lis}</ul>'


# ------------------------------------------------------------------ index.html
def build_index():
    recent = [p for p in PUBS if p["type"] == "article"][:6]
    areas = "".join(f"<li><h3>{e(a['area'])}</h3><p>{e(a['detail'])}</p></li>" for a in DATA["research"]["areas_with_output"])
    recent_li = "".join(f'<li class="ref">{ref_parts(p)}</li>' for p in recent)
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": P["name"],
        "honorificPrefix": P["honorific"],
        "jobTitle": P["position"],
        "worksFor": {"@type": "CollegeOrUniversity", "name": "Universidad Autónoma de Baja California",
                     "department": {"@type": "Organization", "name": P["unit"]}},
        "alumniOf": [{"@type": "CollegeOrUniversity", "name": ed["institution"]} for ed in DATA["education"]],
        "email": "mailto:" + P["email"],
        "identifier": {"@type": "PropertyValue", "propertyID": "ORCID", "value": "0000-0002-7994-9774"},
        "sameAs": [l["url"] for l in P["links"]],
        "knowsAbout": DATA["research"]["keywords"],
    }
    if SITE:
        jsonld["url"] = SITE
        if PHOTO:
            jsonld["image"] = SITE + PHOTO["src"]
    extra = '<script type="application/ld+json">' + json.dumps(jsonld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    html = head(f"{P['name']} — Professor and Researcher, FIAD-UABC", DATA["profile"]["tagline"], "", extra)
    html += "<body>\n" + header("index.html")
    html += f"""<main id="content" tabindex="-1">
<section class="hero">
  <div class="wrap hero-grid">
    <div>
      <div class="hero-id">
        {portrait('portrait')}
        <div>
          <p class="eyebrow">{e(P['honorific'])} · Electronics Engineering</p>
          <h1>{e(P['name'])}</h1>
          <p class="position">{e(P['position'])}<br>{e(P['unit'])}, {e(P['institution'])}<br>{e(P['location'])}</p>
        </div>
      </div>
      <p class="tagline">{e(DATA['profile']['tagline'])}</p>
      {id_links()}
      <p class="cta"><a class="btn" href="cv.html">View full CV</a> <a class="btn btn-ghost" href="downloads/cv-academic.pdf">Download CV (PDF)</a></p>
    </div>
    <aside class="hero-aside" aria-label="Metrics">
      {metrics_block()}
    </aside>
  </div>
</section>

<section class="band" aria-labelledby="profile">
  <div class="wrap narrow">
    <h2 id="profile">Academic profile</h2>
    <p class="lead">{e(DATA['profile']['summary'])}</p>
    {stats_block()}
    <p class="small muted">Counts from the publication record. Chapters include those published with a DOI by Springer and CRC Press; chapters in UABC edited volumes and outreach articles are listed separately in the <a href="cv.html#publications">full CV</a>.</p>
  </div>
</section>

<section class="band band-alt" aria-labelledby="areas">
  <div class="wrap">
    <h2 id="areas">Research areas</h2>
    <ul class="areas">{areas}</ul>
  </div>
</section>

<section class="band" aria-labelledby="recent">
  <div class="wrap narrow">
    <h2 id="recent">Recent journal articles</h2>
    <ol class="refs">{recent_li}</ol>
    <p><a href="cv.html#publications">Full list of publications</a> · <a href="downloads/publications.bib">BibTeX</a></p>
  </div>
</section>

<section class="band band-alt" aria-labelledby="contact-home">
  <div class="wrap narrow">
    <h2 id="contact-home">Contact</h2>
    <p>{e(P['unit'])}, {e(P['institution'])}, {e(P['location'])}.</p>
    <p>Institutional email: <a href="mailto:{e(P['email'])}">{e(P['email'])}</a></p>
  </div>
</section>
</main>
"""
    html += footer()
    (ROOT / "index.html").write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ cv.html
SECTIONS = [
    ("profile", "Profile"), ("research", "Research"), ("education", "Education"),
    ("experience", "Experience"), ("honors", "Honors and awards"), ("publications", "Publications"),
    ("ip", "Intellectual property"), ("projects", "Projects"), ("conferences", "Conferences"),
    ("teaching", "Teaching"), ("supervision", "Supervision"), ("editorial", "Editorial work"),
    ("evaluation", "Evaluation"), ("outreach", "Outreach"), ("other", "Other"),
    ("contact", "Contact"),
]


def sec(sid, title, body):
    return f'<section id="{sid}" class="cv-section" aria-labelledby="{sid}-h"><h2 id="{sid}-h">{e(title)}</h2>{body}</section>\n'


def entry(when, body):
    return f'<li class="entry"><span class="when">{e(when)}</span><div>{body}</div></li>'


def build_cv():
    parts = []
    ids = "".join(
        f"<li><span>{e(i['type'])}</span> " + (f'<a href="{e(i["url"])}">{e(i["value"])}</a>' if i.get("url") else e(i["value"])) + "</li>"
        for i in P["identifiers"])
    parts.append(sec("profile", "Profile", f"""<p class="lead">{e(DATA['profile']['summary'])}</p>
<ul class="kv">{ids}</ul>
{metrics_block()}"""))

    r = DATA["research"]
    reg = "".join(f"<li>{e(x)}</li>" for x in r["lines_registered"])
    areas = "".join(f"<li><strong>{e(a['area'])}.</strong> {e(a['detail'])}</li>" for a in r["areas_with_output"])
    parts.append(sec("research", "Research", f"""<h3>Registered research lines (CVU)</h3><ul>{reg}</ul>
<h3>Areas with published output</h3><ul>{areas}</ul>"""))

    edu = "".join(entry(ed["year"], f"<strong>{e(ed['degree'])}</strong><br>{e(ed['institution'])}"
                        + (f"<br><span class=\"muted\">{e(ed['notes'])}</span>" if ed.get("notes") else "")) for ed in DATA["education"])
    parts.append(sec("education", "Education", f'<ul class="timeline">{edu}</ul>'))

    pos = "".join(entry(f"{x['start']}–{x['end'] or 'present'}", f"<strong>{e(x['role'])}</strong><br>{e(x['org'])}"
                        + (f"<br><span class=\"muted\">{e(x['notes'])}</span>" if x.get("notes") else "")) for x in DATA["positions"])
    stays = "".join(entry(f"{s['start'][:4]}–{s['end'][:4]}", f"<strong>{e(s['type'])}</strong><br>{e(s['org'])}"
                          + (f"<br><span class=\"muted\">{e(s['notes'])}</span>" if s.get("notes") else "")) for s in DATA["stays"])
    serv = "".join(entry(s["period"] or "", e(s["role"]) + (f"<br><span class=\"muted\">{e(s['notes'])}</span>" if s.get("notes") else "")) for s in DATA["service"])
    parts.append(sec("experience", "Professional experience", f"""<ul class="timeline">{pos}</ul>
<h3>Research stays</h3><ul class="timeline">{stays}</ul>
<h3>Academic leadership and service</h3><ul class="timeline">{serv}</ul>"""))

    dis = "".join(entry(d["year"], f"<strong>{e(d['name'])}</strong><br>{e(d['org'])}"
                        + (f"<br><span class=\"muted\">{e(d['notes'])}</span>" if d.get("notes") else "")) for d in DATA["distinctions"])
    parts.append(sec("honors", "Honors and awards", f'<ul class="timeline">{dis}</ul>'))

    years = sorted({p["year"] for p in PUBS}, reverse=True)
    type_opts = "".join(f'<option value="{t}">{e(TYPE_LABEL[t])} ({COUNT[t]})</option>' for t in TYPE_LABEL if COUNT[t])
    year_opts = "".join(f'<option value="{y}">{y}</option>' for y in years)
    filt = f"""<form class="filters" id="pub-filters" hidden aria-label="Filter publications">
  <div class="field"><label for="f-type">Type</label><select id="f-type"><option value="">All</option>{type_opts}</select></div>
  <div class="field"><label for="f-year">Year</label><select id="f-year"><option value="">All</option>{year_opts}</select></div>
  <div class="field grow"><label for="f-text">Search title, authors or venue</label><input id="f-text" type="search" autocomplete="off"></div>
  <div class="field"><button type="reset" class="btn btn-ghost">Reset</button></div>
  <p class="filter-status" id="f-status" role="status" aria-live="polite"></p>
</form>
<p class="empty" id="f-empty" hidden>No publications match the filters. <button type="button" class="linklike" id="f-clear">Reset filters</button></p>"""
    blocks = []
    for t, label in TYPE_LABEL.items():
        items = [p for p in PUBS if p["type"] == t]
        if not items:
            continue
        lis = []
        for p in items:
            extra = f' <span class="tag">{e(p["label"])}</span>' if p.get("label") else ""
            for rid in p.get("related") or []:
                rp = BY_ID.get(rid)
                if rp and rp.get("doi"):
                    kind = "Published version" if p["type"] == "preprint" else "Preprint version"
                    extra += f' <span class="related">{kind}: <a href="https://doi.org/{e(rp["doi"])}">{e(rp["doi"])}</a></span>'
            search = " ".join([p["title"], p.get("venue") or "", " ".join(a["family"] for a in p["authors"] + (p.get("editors") or []))])
            lis.append(f'<li class="ref" data-type="{t}" data-year="{p["year"]}" data-search="{e(search.lower())}">{ref_parts(p)}{extra}</li>')
        note = ""
        if t == "proceedings":
            note = '<p class="small muted">The four WIT Press papers (2008–2011) come from the ORCID record and were verified in Crossref; they are not listed in the CVU.</p>'
        if t == "other":
            note = '<p class="small muted">Classified as outreach publications in the CVU; includes a 2025 article in Revista ELECTRO listed in ORCID.</p>'
        blocks.append(f'<div class="pub-group" data-group="{t}"><h3>{e(label)} <span class="count">({len(items)})</span></h3>{note}<ol class="refs" reversed>{"".join(lis)}</ol></div>')
    ds = "".join(f'<li><a href="{e(d["url"])}">{e(d["title"])}</a> — {e(d["description"])}</li>' for d in DATA["data_software"])
    parts.append(sec("publications", "Publications", f"""{stats_block()}
<p class="small muted">IEEE reference style. Authors in published order; the CV holder's name is in bold. Titles are given in their original language. Every DOI was checked against Crossref on {long_date(DATA['meta']['updated'])}.</p>
{filt}
{''.join(blocks)}
<div class="pub-group static"><h3>Data and code in public repositories</h3><ul>{ds}</ul></div>"""))

    ip = DATA["ip"]
    pat = "".join(f"<li><strong>{e(x['title'])}</strong>. Patent {e(x['number'])}, application {e(x['application'])} filed {long_date(x['filed'])}. {e(x['status'])}. Holders/inventors: {e(x['holders'])}.</li>" for x in ip["patents"])
    sw = "".join(f"<li>{e(x['title'])}. Registration {e(x['number'])} ({x['year']}).</li>" for x in ip["software"])
    parts.append(sec("ip", "Intellectual property", f"""<h3>Patents</h3><p class="small muted">Titles in the original Spanish.</p><ul class="plain">{pat}</ul>
<h3>Software copyright registrations</h3><p class="small muted">{e(ip['software_note'])}</p><ul class="plain">{sw}</ul>"""))

    prj = "".join(entry(f"{x['start'][:4]}–{x['end'][:4]}", f"<strong>{e(x['title'])}</strong><br>{e(x['org'])}") for x in DATA["projects"])
    parts.append(sec("projects", "Research projects", f'<p class="small muted">{e(DATA["projects_note"])}</p><ul class="timeline">{prj}</ul>'))

    tk = "".join(entry(t["year"], f"{e(t['title'])}. <i>{e(t['event'])}</i>, {e(t['country'])}. <span class=\"muted\">{e(t['kind'])}.</span>") for t in DATA["talks"])
    parts.append(sec("conferences", "Conference presentations", f'<p class="small muted">{len(DATA["talks"])} oral presentations, posters, full papers and keynotes recorded in the CVU. Titles in their original language.</p><ul class="timeline compact">{tk}</ul>'))

    tch = DATA["teaching"]
    grp = "".join(f"<h3>{e(g['level'])}</h3><p class=\"muted small\">{e(g['period'])}</p><ul class=\"cols\">" + "".join(f"<li>{e(c)}</li>" for c in g["courses"]) + "</ul>" for g in tch["groups"])
    cur = "".join(entry(c["year"], f"{e(c['title'])}. <span class=\"muted\">{e(c['notes'])}</span>") for c in tch["curriculum"])
    parts.append(sec("teaching", "Teaching", f"""<p>{e(tch['summary'])}</p>{grp}<h3>Curriculum design</h3><ul class="timeline">{cur}</ul>"""))

    th_blocks = []
    names = {"Ph.D.": "Doctoral theses", "M.Sc.": "Master's theses", "B.Sc.": "Undergraduate theses"}
    for lvl in LEVELS:
        items = sorted([t for t in THESES if t["level"] == lvl], key=lambda t: -t["year"])
        lis = "".join(entry(t["year"], e(t["title"]) + (f". {e(t['student'])}" if t.get("student") else "")
                            + f". <span class=\"muted\">{e(t['role'])} · {e(t['institution'])}</span>") for t in items)
        th_blocks.append(f"<h3>{names[lvl]} <span class=\"count\">({len(items)})</span></h3><ul class=\"timeline compact\">{lis}</ul>")
    com = "".join(entry(c["year"], f"{e(c['title'])}. <span class=\"muted\">{e(c['role'])}, {e(c['level'])}, {e(c['institution'])}</span>") for c in DATA["thesis_committees"])
    parts.append(sec("supervision", "Student supervision", f"""<p>{len(THESES)} theses supervised or co-supervised: {TH_COUNT['Ph.D.']} doctoral, {TH_COUNT['M.Sc.']} master's and {TH_COUNT['B.Sc.']} undergraduate. The year shown is the year the degree was awarded; titles are in their original language.</p>
{''.join(th_blocks)}<h3>Thesis committees and examination boards</h3><ul class="timeline compact">{com}</ul>"""))

    ed = "".join(entry(x["period"], f"<strong>{e(x['role'])}</strong>, <i>{e(x['venue'])}</i>" + (f". {e(x['detail'])}" if x.get("detail") else "")) for x in DATA["editorial"])
    rv = "".join(f"<li>{e(j)}</li>" for j in DATA["reviewing"]["journals"])
    parts.append(sec("editorial", "Editorial work and peer review", f"""<ul class="timeline">{ed}</ul>
<p class="small">Editor of the book <i>Machine Learning for Complex and Unmanned Systems</i> (CRC Press, 2024).</p>
<h3>Peer review</h3><p class="small muted">{e(DATA['reviewing']['summary'])}</p><ul class="cols">{rv}</ul>"""))

    ev = "".join(f"<li><strong>{e(x['org'])}.</strong> {e(x['detail'])}</li>" for x in DATA["evaluation"])
    parts.append(sec("evaluation", "Evaluation and review panels", f'<ul class="plain">{ev}</ul>'))

    org = "".join(entry(x["year"], e(x["detail"])) for x in DATA["organization"])
    out = "".join(entry(x["year"], e(x["detail"])) for x in DATA["outreach"])
    parts.append(sec("outreach", "Event organization and outreach", f"""<h3>Event organization</h3><ul class="timeline compact">{org}</ul>
<h3>Science outreach</h3><ul class="timeline compact">{out}</ul>"""))

    tr = "".join(entry(x["year"], f"{e(x['title'])}. {e(x['org'])}.") for x in DATA["training"])
    lg = "; ".join(e(l["language"]) + (f" ({e(l['level'])})" if l.get("level") else "") for l in DATA["languages"])
    parts.append(sec("other", "Further training and languages", f"""<ul class="timeline compact">{tr}</ul><p><strong>Languages:</strong> {lg}.</p>"""))

    parts.append(sec("contact", "Contact", f"""<p>{e(P['unit'])}, {e(P['institution'])}, {e(P['location'])}.</p>
{id_links('id-links id-links-block')}
<p class="small muted">Content last updated: {UPDATED}.</p>"""))

    toc = "".join(f'<li><a href="#{sid}">{e(t)}</a></li>' for sid, t in SECTIONS)
    html = head(f"Curriculum Vitae — {P['name']}", "Full academic CV: education, experience, publications, teaching and student supervision.", "cv.html")
    html += "<body class=\"cv\">\n" + header("cv.html")
    html += f"""<main id="content" tabindex="-1">
<div class="wrap cv-head">
  <div class="cv-id">
    {portrait('portrait portrait-cv')}
    <div>
      <p class="eyebrow">Curriculum Vitae</p>
      <h1>{e(P['honorific'])} {e(P['name'])}</h1>
      <p class="position">{e(P['position'])}<br>{e(P['unit'])}, {e(P['institution'])} · {e(P['location'])}</p>
      {id_links()}
    </div>
  </div>
  <div class="cv-actions"><a class="btn btn-ghost" href="downloads/cv-academic.pdf">PDF</a> <a class="btn btn-ghost" href="downloads/cv-academic.md">Markdown</a> <a class="btn btn-ghost" href="downloads/publications.bib">BibTeX</a> <button type="button" class="btn btn-ghost js-only" id="print-btn" hidden>Print</button></div>
</div>
<div class="wrap cv-layout">
  <nav class="toc" aria-label="CV sections"><p class="toc-title">Sections</p><ol>{toc}</ol></nav>
  <div class="cv-body">
{''.join(parts)}  </div>
</div>
</main>
"""
    html += footer()
    (ROOT / "cv.html").write_text(html, encoding="utf-8")


# ------------------------------------------------------------------ Markdown
def build_md():
    L = [f"# {P['honorific']} {P['name']}", "", f"{P['position']}  ", f"{P['unit']}, {P['institution']}  ", f"{P['location']}  ",
         f"Email: {P['email']}  ", "ORCID: https://orcid.org/0000-0002-7994-9774", "", f"*Updated on {UPDATED}.*", "",
         "## Profile", "", DATA["profile"]["summary"], "",
         f"Citation metrics ({M['source']}, accessed {long_date(M['retrieved'])}): {M['citations']:,} citations; h-index = {M['h_index']}; i10-index = {M['i10_index']}. {M['note']}", "",
         "## Education", ""]
    L += [f"- **{ed['degree']}**, {ed['institution']}, {ed['year']}." + (f" {ed['notes']}" if ed.get("notes") else "") for ed in DATA["education"]]
    L += ["", "## Professional experience", ""]
    L += [f"- {x['start']}–{x['end'] or 'present'}: **{x['role']}**, {x['org']}." + (f" {x['notes']}" if x.get("notes") else "") for x in DATA["positions"]]
    L += [f"- {s['start'][:4]}–{s['end'][:4]}: {s['type']}, {s['org']}." for s in DATA["stays"]]
    L += [f"- {s['role']}" + (f" ({s['period']})." if s.get("period") else ".") + (f" {s['notes']}" if s.get("notes") else "") for s in DATA["service"]]
    L += ["", "## Honors and awards", ""]
    L += [f"- {d['year']}: {d['name']}. {d['org']}." + (f" {d['notes']}" if d.get("notes") else "") for d in DATA["distinctions"]]
    L += ["", "## Publications", "", "IEEE style. The CV holder's name is in bold. Titles in their original language.", ""]
    for t, label in TYPE_LABEL.items():
        items = [p for p in PUBS if p["type"] == t]
        if items:
            L += [f"### {label} ({len(items)})", ""] + [f"{i}. {ref_parts(p, 'md')}" for i, p in enumerate(items, 1)] + [""]
    L += ["### Data and code", ""] + [f"- [{d['title']}]({d['url']}): {d['description']}" for d in DATA["data_software"]]
    L += ["", "## Intellectual property", "", "### Patents", ""]
    L += [f"- {x['title']}. Patent {x['number']}, application {x['application']} ({long_date(x['filed'])}). {x['status']}. {x['holders']}." for x in DATA["ip"]["patents"]]
    L += ["", "### Software copyright registrations (INDAUTOR)", ""] + [f"- {x['title']}. Registration {x['number']} ({x['year']})." for x in DATA["ip"]["software"]]
    L += ["", "## Research projects", ""] + [f"- {x['start'][:4]}–{x['end'][:4]}: {x['title']}. {x['org']}." for x in DATA["projects"]]
    L += ["", "## Conference presentations", ""] + [f"- {t['year']}. {t['title']}. *{t['event']}*, {t['country']}. {t['kind']}." for t in DATA["talks"]]
    L += ["", "## Teaching", "", DATA["teaching"]["summary"], ""]
    for g in DATA["teaching"]["groups"]:
        L += [f"**{g['level']}** ({g['period']}): " + "; ".join(g["courses"]) + ".", ""]
    L += [f"- {c['year']}: {c['title']}. {c['notes']}" for c in DATA["teaching"]["curriculum"]]
    L += ["", "## Student supervision", "",
          f"{len(THESES)} theses supervised or co-supervised: {TH_COUNT['Ph.D.']} doctoral, {TH_COUNT['M.Sc.']} master's and {TH_COUNT['B.Sc.']} undergraduate.", ""]
    for lvl in LEVELS:
        L += [f"### {lvl}", ""]
        L += [f"- {t['year']}. {t['title']}." + (f" {t['student']}." if t.get("student") else "") + f" {t['role']}, {t['institution']}."
              for t in sorted([t for t in THESES if t["level"] == lvl], key=lambda t: -t["year"])] + [""]
    L += ["### Thesis committees", ""] + [f"- {c['year']}. {c['title']}. {c['role']}, {c['level']}, {c['institution']}." for c in DATA["thesis_committees"]]
    L += ["", "## Editorial work and peer review", ""] + [f"- {x['period']}: {x['role']}, *{x['venue']}*" + (f". {x['detail']}." if x.get("detail") else ".") for x in DATA["editorial"]]
    L += ["", "Peer review: " + "; ".join(DATA["reviewing"]["journals"]) + "."]
    L += ["", "## Evaluation and review panels", ""] + [f"- **{x['org']}.** {x['detail']}" for x in DATA["evaluation"]]
    L += ["", "## Event organization and outreach", ""] + [f"- {x['year']}: {x['detail']}" for x in DATA["organization"] + DATA["outreach"]]
    L += ["", "## Further training", ""] + [f"- {x['year']}: {x['title']}. {x['org']}." for x in DATA["training"]]
    L += ["", "## Languages", "", "; ".join(l["language"] + (f" ({l['level']})" if l.get("level") else "") for l in DATA["languages"]) + ".", ""]
    (ROOT / "downloads" / "cv-academic.md").write_text("\n".join(L), encoding="utf-8")


# ------------------------------------------------------------------ BibTeX
def tex(s):
    s = str(s)
    for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("$", "\\$"), ("#", "\\#"), ("_", "\\_")):
        s = s.replace(a, b)
    return s


def bibkey(p, used):
    fam = (p["authors"] or p.get("editors") or [{"family": "anon"}])[0]["family"]
    fam = unicodedata.normalize("NFKD", fam).encode("ascii", "ignore").decode()
    fam = re.sub(r"[^A-Za-z]", "", fam.split("-")[0].split(" ")[0]) or "anon"
    word = next((w for w in re.findall(r"[A-Za-z]+", unicodedata.normalize("NFKD", p["title"]).encode("ascii", "ignore").decode())
                 if len(w) > 3), "x")
    k = base = f"{fam.lower()}{p['year']}{word.lower()}"
    n = 1
    while k in used:
        n += 1
        k = f"{base}{n}"
    used.add(k)
    return k


def build_bib():
    used, out = set(), [f"% Publications of {P['name']}. Generated from data/cv.public.json ({DATA['meta']['updated']}).", ""]
    kinds = {"article": "article", "other": "article", "chapter": "incollection", "chapter_inst": "incollection",
             "proceedings": "inproceedings", "book": "book", "preprint": "misc"}
    for p in PUBS:
        f = OrderedDict()
        if p["authors"]:
            f["author"] = " and ".join(f"{a['family']}, {a['given']}".strip(", ") for a in p["authors"])
        if p.get("editors") and p["type"] in ("book", "chapter"):
            f["editor"] = " and ".join(f"{a['family']}, {a['given']}".strip(", ") for a in p["editors"])
        f["title"] = "{" + tex(p["title"]) + "}"
        if p["type"] in ("article", "other"):
            f["journal"] = p["venue"]
        elif p["type"] in ("chapter", "chapter_inst"):
            f["booktitle"] = p["venue"]
            if p["type"] == "chapter_inst":
                f["chapter"] = p.get("chapter")
            if p.get("series"):
                f["series"] = p["series"]
        elif p["type"] == "proceedings":
            f["booktitle"] = p["venue"]
        elif p["type"] == "preprint":
            f["howpublished"] = p["venue"]
            f["note"] = "Preprint"
        f["year"] = p["year"]
        for k in ("volume", "issue", "pages", "article_number", "publisher", "isbn", "doi", "url"):
            v = p.get(k)
            if not v or (k == "url" and p.get("doi")):
                continue
            key = {"issue": "number", "article_number": "eid"}.get(k, k)
            f[key] = str(v).replace("–", "--") if k == "pages" else v
        body = ",\n".join(f"  {k} = {{{tex(v) if k not in ('title', 'url', 'doi') else v}}}" for k, v in f.items() if v)
        out.append(f"@{kinds[p['type']]}{{{bibkey(p, used)},\n{body}\n}}\n")
    (ROOT / "downloads" / "publications.bib").write_text("\n".join(out), encoding="utf-8")


def build_sitemap():
    if not SITE:
        return
    d = DATA["meta"]["updated"]
    urls = "".join(f"  <url><loc>{e(SITE + u)}</loc><lastmod>{d}</lastmod></url>\n" for u in ("", "cv.html"))
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")


if __name__ == "__main__":
    build_index()
    build_cv()
    build_md()
    build_bib()
    build_sitemap()
    print("Built: index.html, cv.html, downloads/cv-academic.md, downloads/publications.bib, sitemap.xml")
