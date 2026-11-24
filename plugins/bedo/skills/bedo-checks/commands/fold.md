# `fold`

**When:** every day, in a scheduled Code session nobody is watching; and on call

**Command:** `fold` (today, by her clock; `--date YYYY-MM-DD` for another day)

**The amendments are worked down a little every day** (23 Nov 2026, her words: it would be nice if we could get into a daily amendment fold). The weekly fold showed her a list on Sundays and the pile grew between them: that day 72 rows were active and 50 named no check. `fold` prints one day's share, read live, the count first. It reads; it never writes. The session does the work and asks her nothing.

Its lists, in the order to work them:

- **`mark folded`**: rows the mapping says have landed (`amendment_checks` in the `facts_local` settings row). Open each line's evidence on `main` before anything is marked: the check it names in `core/bedo_rules.py` and the code behind it, or the rule's own words in `docs/v53-judgment.md`. A mapping can be wrong. Evidence there: set the row's status to `folded` through the connector, and add one line to the end of its detail, `[be•do] folded <D Mon YYYY> by the daily fold: <where it lives>`, the rest carried forward verbatim. Evidence missing: take the row out of the mapping, so the next run lists it to build.
- **`built, mark folded once its pull request is merged`**: what an earlier run built. Read the pull request. Merged: drop its `pr:N` from the mapping, then mark the row as above. Still open: leave it. Closed without merging: drop the row's whole entry from the mapping and say so in the run's record.
- **`new`** and **`the oldest of the backlog`**: rows that haven't landed. Read the whole row first (her words are in its detail), then decide where it lives:
  - **already there**: most of the older rows are. Look in the judgment file and the code before building anything; a rule already in force needs only its mapping;
  - a rule code can check → the check, its test, and its name in `CHECKS`;
  - a string, a glyph or a threshold → `facts.json`;
  - anything of hers (a name, a service, a place, an id) → her settings row, never the repo (J15);
  - a rule that needs a model → one line in `docs/v53-judgment.md`, under the section it belongs to, her words and their date kept;
  - a procedure → that skill's `SKILL.md`;
  - a row with no decision written, one a later row replaced, or one only she can settle → it stays active. Add one `[be•do]` line saying what it waits on and put it on the run's short list. Never guess a rule she didn't state, and never fold a row because it is old.

  Then name where it landed in the mapping: the check names or `judgment`, and `pr:N` beside them when the evidence is in a pull request and not on `main` yet.

**A row is folded only when its evidence is on `main`.** What was already there and only lacked its mapping is marked the same day. What a run builds waits for its pull request: her accept is her yes, and the next run after the merge marks it.

**One pull request, never a pile.** A day's building is one branch and one pull request, titled `The daily fold, <D Mon>`, tests green and `outgoing` at `0 hit(s)` (J10). Its description gives each amendment one line: the rule, never a name, and where it landed. While an earlier fold pull request is still open, add the day's commits to its branch and its description. If this session can't push there, build nothing today, do the marking, and say so. Never merge: that is hers.

**The mapping is one careful edit.** Read the `facts_local` row's JSON, change only `amendment_checks`, check that it still parses and that every other key is unchanged, write it back through the connector, and run `BEDO_FRESH=1 run_checks.sh fold` to see the lists move. A write that fails or a row that doesn't parse after it: put the earlier text back and stop.

**The run's record** is its session entry: one ⚡ row under the be•do drive, with none of her time on it. It gives the count before and after (`71 active → 58`), what was marked, what was built and the pull request's link, and the short list that is hers, if there is one. Nothing is sent to her phone at night; Duet says the line in the morning's summary, last (J17).

The sizes are `fold.daily` in `facts.json`: how far back a row counts as new, how many of the oldest a day takes, and how many landed rows a day marks. The quest's data row is kept active by rule and never listed. The weekly close's fold reads back what the week's runs folded, and a line she fixes reopens its row.
