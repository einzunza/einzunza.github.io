# Academic website — Everardo Inzunza-González

Static website (plain HTML, CSS and JavaScript) with the profile and curriculum vitae of Dr. Everardo Inzunza-González, Full Professor and Researcher at FIAD, Universidad Autónoma de Baja California (UABC), Mexico. It is served by GitHub Pages with no build step: the HTML files are already generated and committed.

Live site: <https://einzunza.github.io/>

## Structure

```text
index.html                    Home: profile, research areas, recent articles, contact
cv.html                       Full CV with side index and publication filters
assets/css/styles.css         Screen and print styles (no external fonts or resources)
assets/js/main.js             Progressive enhancement: filters, current section, print button
assets/img/                   Portrait (metadata removed)
data/cv.public.json           Single source of public data
downloads/cv-academic.pdf     CV as PDF, printed from cv.html
downloads/cv-academic.md      CV in Markdown
downloads/publications.bib    Bibliography in BibTeX
sitemap.xml                   Sitemap for the two pages
tools/build.py                Rebuilds index.html, cv.html, .md, .bib and sitemap.xml from the JSON
tools/make_pdf.py             Rebuilds the PDF with headless Chrome and cleans its metadata
.nojekyll                     Tells GitHub Pages to serve files as they are, without Jekyll
```

All internal paths are relative, so the site works as a user site (`https://einzunza.github.io/`) or as a project site.

## Preview

Open `index.html` in a browser, or serve the folder locally:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/
```

Without JavaScript all content remains visible; only the filters and the section highlighting are lost.

## Editing

1. Edit `data/cv.public.json`. Each publication has `type` (`article`, `book`, `chapter`, `proceedings`, `preprint`, `other`, `chapter_inst`), `year`, `title` as published, `authors` in published order (`given`, `family`, `me`), `venue`, `volume`, `issue`, `pages` or `article_number`, `doi` and, when there is no DOI, `url`.
2. Rebuild: `python3 tools/build.py`
3. Rebuild the PDF (optional): `python3 tools/make_pdf.py` (requires Google Chrome and `pip install pypdf`).
4. Check `index.html` and `cv.html` in a browser, then commit and push.

The build script escapes all text before inserting it into HTML. Nothing is fetched from ORCID, Crossref or Google Scholar on page load; those sources were queried once and the reviewed result is stored in the JSON.

- For a publication with a DOI, copy title, authors, journal, volume, issue and pages from Crossref (`https://api.crossref.org/works/<DOI>`) and check that the DOI resolves to the right work.
- Citation metrics (`metrics`) must be updated by hand, together with their access date.
- `meta.settings.show_student_names` records whether student names are published in the supervision list. It is currently `false` and the public JSON contains no student names.

## Publishing

The repository `einzunza/einzunza.github.io` is published from branch `main`, folder `/` (Settings → Pages → Build and deployment → Deploy from a branch). Every push to `main` redeploys the site within a few minutes.

## License

No license has been chosen for the content or the code. All rights reserved until one is selected.
