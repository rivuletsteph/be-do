---
name: "grant-watch"
description: "The weekly grant watch: upcoming federal deadlines and new funding opportunities that match a watch list, plus programs applied to before that are open again, from grants.gov's public API. Use when the weekly grant watch fires, or when she asks about grant deadlines, funding opportunities, or what's been applied for."
---

# Grant watch

A weekly report of funding opportunities that match a watch list: what closes
in the next weeks, what is new since last week, and which programs applied to
before are open again. It runs every week from a scheduled task, or whenever
she asks.

**Nothing personal lives here, and no internal document ever does.** The watch
list is program-level facts only: program names, opportunity and award
numbers, cycles, years, status, role and topic words. No budgets, salaries or
personnel, ever. Those stay in her university's tools.

## The page is the record

**One page holds everything** (her word, 6 Nov 2026: no Sheet on her personal
account). Her grant watch artifact is both what she reads and where the data
lives: a `<script type="application/json" id="grant-watch-data">` block inside
it carries the whole watch list and last week's seen ids. There is no
spreadsheet.

The data has these parts:

- `applied`: one row per opportunity from her Copilot pull (program, agency,
  number, cycle, year, status, role, keywords, evidence). `evidence` is her
  mail's subject line. It stays in her own page and is left out of a shared
  file.
- `funded`: funded projects from public sources (project, funder, program,
  number, years, role, partners, keywords, confirmed, checked, source).
  `checked` opens with yes, partly, likely or not yet, then the reason, so a
  reader can verify it.
- `keywords` (a phrase is searched as a phrase), `agencies` (grants.gov codes
  such as `USDA-NIFA`), `programs` (an opportunity number without its last
  part, such as `USDA-NIFA-NLGCA`), `assistance_listings` (such as `10.326`),
  `ignore`, `ignore_agencies`.

To read it back, take the page with the Artifact tool's read, save it, and run
`scripts/grant_page.py --extract page.html watch.json seen.json`. A change she
asks for (a new search term, a row confirmed) goes into `watch.json`. Then
rebuild the page and republish it to the same link.

## Run it

```
python3 scripts/grant_watch.py watch.json --seen seen.json [--weeks 12] [--json]
```

- It needs `api.grants.gov`. Searches are POSTs, because the API refuses a GET.
  If the host can't be reached, it exits 2. Say so in one line, and never fill
  the report in from memory.
- `--seen` is last week's ids, from the page. The script rewrites the file
  with this week's ids, and the rebuilt page carries them forward. On a first
  run nothing counts as new yet.
- NIFA's own funding pages (nifa.usda.gov) load over HTTP/1.1 but have been
  flaky over HTTP/2. grants.gov carries every NIFA opportunity, so it is the
  source and NIFA's site is only a cross-check.

## The report

Three parts, each line with the program, agency, number, close date and days
left, and the grants.gov link:

1. **Deadlines coming up** within the window (12 weeks by default).
2. **New since last week**: matches not seen before that close later.
3. **Applied before, open again**: a program from the applied tab that has a
   new cycle.

**Two outputs each week:**

1. Her page: `scripts/grant_page.py report.json watch.json grant-watch.html`,
   republished to the same artifact link. It is private to her and carries the
   full data.
2. The file to share: the same with `--standalone`, saved as
   `grant-watch-YYYY-MM-DD.html` and sent to her with SendUserFile, so she can
   save it to OneDrive and pass it to colleagues. It leaves out her mail's
   subject lines.

The page leads with what fits the work: a program applied to before, a watched
program or agency, or a keyword in the title. Funded projects come next. The
rest (a keyword found only in a long description) is folded away. Give her the
nearest fitting deadlines in chat (three lines at most) with the page link.
Opportunities that keep showing up and never fit go into `ignore` or
`ignore_agencies` *with her yes*. Nothing is dropped on be•do's own call.
