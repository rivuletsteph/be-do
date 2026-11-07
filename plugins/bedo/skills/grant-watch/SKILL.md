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
list is a Google Sheet in her Drive. It holds program-level facts only: program
names, opportunity numbers, cycles, years, status, role and topic words. No
budgets, salaries or personnel, ever. Those stay in her university's tools.

## The watch list (the Sheet)

Three tabs:

- **applied**: one row per opportunity, pasted from her Copilot pull. Columns:
  program, agency, number, cycle, year, status, role, keywords, evidence.
- **interests**: one column per kind. Fill `keywords` (a phrase is searched as
  a phrase), `agencies` (grants.gov codes such as `USDA-NIFA`), `programs`
  (an opportunity number without its last part, such as `USDA-NIFA-NLGCA`, so
  every cycle is caught), `assistance_listings` (such as `10.326`),
  `ignore_agencies` and `ignore`.
- **funded**: projects that were funded, from public sources (news releases,
  NIFA records, paper acknowledgments). Columns: project, funder, program, award
  number, years, his role, partners, keywords, confirmed, checked by Claude,
  source. They go into `watch.json` as `funded` and show on the page. A row is
  marked checked only when a source was read and names him.
- **reports**: one block per week, newest at the top, plus the `seen` ids the
  next run compares against.

Read the first two tabs and turn them into `watch.json`, shaped like
`assets/watch.example.json`. An applied row's number brings its program back
into the watch automatically.

## Run it

```
python3 scripts/grant_watch.py watch.json --seen seen.json [--weeks 12] [--json]
```

- It needs `api.grants.gov`. Searches are POSTs, because the API refuses a GET.
  If the host can't be reached, it exits 2. Say so in one line, and never fill
  the report in from memory.
- `--seen` is last week's ids, which the reports tab holds. The script rewrites
  the file with this week's ids, and those go back into the tab. On a first run
  nothing counts as new yet.
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

**The file is what gets shared** (her word, 6 Nov 2026: not a Sheet on her
personal account). `--standalone` without `--sheet` writes one whole HTML
document she saves to OneDrive and shares with colleagues. The Sheet stays
private to her and is never shared. Each funded row shows why it is checked or
likely, so a reader can confirm it.

**She reads it as a page** (her word, 6 Nov 2026: much easier to read than
the Sheet). Build it with `scripts/grant_page.py report.json watch.json
grant-watch.html --sheet <Sheet link>` and republish the one grant watch
artifact, keeping its link. The page leads with what fits the work: a program
applied to before, a watched program or agency, or a keyword in the title. The
rest (a keyword found only in a long description) is folded away. Write the
rows at the top of the reports tab too, and give her the nearest fitting
deadlines in chat (three lines at most) with the page link. Opportunities that keep showing up
and never fit go into `ignore` or `ignore_agencies` *with her yes*. Nothing is
dropped on be•do's own call.
