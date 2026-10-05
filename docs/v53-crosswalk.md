# V53 crosswalk — where every V52 section and active amendment goes

V53 is V52 and its active amendments rebuilt around *log what matters*, in four places:

| place | what lives there | how it runs |
|---|---|---|
| **code** | a check that is enforced and tested — `plugins/bedo/core`, the builders, `close.py` | **code ✓** is built and tested now; **code** names the slot it goes into next |
| **facts** | ids, choice strings, glyphs, orders, thresholds — `core/facts.json` (ships), `facts_local.json` (hers, never ships), and the practices catalog read live | read at run time, never recalled |
| **judgment** | a short rule a model needs — `docs/v53-judgment.md`, section J# | loaded whole, every chat |
| **drop** | cut, with one line on why | **drop** that touches what she logs or sees took her yes; **drop · superseded** is a rule a later one already replaced; **drop · state** is week state, not a rule |

**V52, 140 rows** (each heading; the sixteen invariants one row each): code ✓ 42 · code 6 · facts 15 · judgment 57 · drop 20.  
**Active amendments, 263 rows:** code ✓ 72 · code 19 · facts 25 · judgment 105 · drop 42.  
Every row is placed once. 114 rows are enforced in code today.

Amendments are listed by number in date order (A1 is the oldest active row, 15 Aug 2026). Her own titles and the record ids are in her copy of this file in Drive; the repo holds no ids and no names.

## The drops that needed her yes — all five accepted, 4 Oct 2026

Only these touched what she logs or sees. She said yes to all five on 4 Oct 2026. Everything else placed **drop** is plumbing or already replaced.

1. **Stop asking how work sessions felt.** Feelings are asked only on the moments that carry meaning — highlights, glimmers, noticing, journal, dreams, time with people. The weekly *depth* flag goes with it. (V52 QA check · A52 · A67)
2. **Drop the weekly backlog bucket.** The monthly ahead-review already is the triage. (V52 one bucket a week · A35's weekly part)
3. **Drop the *still true?* strip of the five oldest ▶️ rows from the day ahead.** The three recommendations and the monthly review cover it. (V52 the rest · A112)
4. **Stop the twice-daily token readings, the daily summary line and the weekly friction review.** The close notes the 15% line only when the meter can be read. (V52 usage, the token budget, the budget page)
5. **Retire what already stopped running:** the ring read per phase, the promote checkbox, a monthly intention word, per-diem tracking. Fields stay; nothing asks for them. (A40 · A61 · A107 · A137 · the ring in V52 readings)

## V52, section by section

| # | V52 section | place | where in V53 | note |
|---|---|---|---|---|
| 2 | What changed from V51 | drop | — | history; the git log and this crosswalk carry it |
| 3 | How to read this | judgment | J0 | lines and tables; a rule lives where it is used |
| 4 | The load contract | drop | — | plumbing: replaced by code plus a judgment file small enough to load whole (~14 k) |
| 5 | The governing principle | judgment | J0 | every rule constrains be•do; invariant · default · observation |
| 6 | be•do's design principles | judgment | J1 | catch the small things, north star, longpath |
| 7 | The one rule — ask when supplying | judgment | J3 | I1's preview = write half goes to code (entry writer, next) |
| 8 | The shape of a reply | judgment | J4 |  |
| 9a | I1 preview = write | code | next: entry writer renders the check and writes in one call | bedo_entry.problems is the first half, built |
| 9b | I2 verify the base | code ✓ | core/bedo_preflight: base by name, newest row within 36 h, else stop | base by name, newest row within ~36 h |
| 9c | I3 ask before supplying | judgment | J3 |  |
| 9d | I4 full labelled choices | code ✓ | core/bedo_entry; facts.json strings from the live schema |  |
| 9e | I5 the chain is append-only; latest action row wins | code ✓ | core/bedo_reader chain_key + resolve | logs sharing a key's minute are their own rows |
| 9f | I6 correct in place | judgment | J3 |  |
| 9g | I7 never assert absence without looking | judgment | J3 |  |
| 9h | I8 never retract verified work | judgment | J3 |  |
| 9i | I9 irreversible writes need consent | judgment | J3, J14 |  |
| 9j | I10 every amendment row is active | facts | facts.json amendment_status | the base's field default |
| 9k | I11 a truncated read is not a read | code ✓ | core/bedo_reader.complete, used by every builder and the close | day_digest had no check; it has one now |
| 9l | I12 re-read the clock; store UTC | code ✓ | core/bedo_entry (UTC with Z); drift check next in preflight |  |
| 9m | I13 no frozen copy, no personal data in code | code ✓ | tools/privacy_check.py; facts_local.json gitignored |  |
| 9n | I14 a late close lives in two bases | code ✓ | builders read this week and last; bedo_split reads the outgoing base |  |
| 9o | I15 dedupe by record id, live first | code ✓ | core/bedo_reader.merge_live_first | lifted out of four loaders into one |
| 9p | I16 the split's delete set from ids | code ✓ | core/bedo_split.plan, both asserts | reproduces the W40 close's 766 exactly |
| 10 | COMMON (part header) | drop | — | no load parts in V53 |
| 11 | Purpose | judgment | J1 | coherence; nothing has to converge; tone |
| 12 | What be•do does not do | judgment | J4 |  |
| 13 | Preflight | code ✓ | core/bedo_preflight | the read-the-amendments-before-blaming-the-base line → J0 |
| 14 | Symbols | facts | facts.json status, phase, attention, day_emoji | ✖️ means she decided → J12 |
| 15 | Glyphs, I4 and the drift rule | facts | facts.json glyph_codepoints; core/bedo_entry checks strings |  |
| 16 | Emotion | facts | facts.json emotion | offering words → J6 |
| 17 | Wellness | facts | facts.json wellness; palette in the page engines |  |
| 18 | Effort bands | facts | facts.json effort; computed in look-behind |  |
| 19 | Practices — one flat list | facts | the catalog, read live; norm() in bedo_common |  |
| 20 | Cadence | facts | catalog CADENCE: line | display rule superseded by A208 |
| 21 | The Entry Check | code ✓ | core/bedo_entry.problems | rendering the preview stays with the writer |
| 22 | The remaining list every turn | code ✓ | core/bedo_remaining from a live catalog read; J8 says it ends every reply |  |
| 23 | Two voices | code ✓ | core/bedo_entry (one divider), core/bedo_export.hers | her words verbatim → J5 |
| 24 | Person tagging | judgment | J7 |  |
| 25 | person vs mentioned | judgment | J7 |  |
| 26 | Whose day a row belongs to | code | next: his day page | derived, never stored |
| 27 | Logging | judgment | J2 | time spent xor end → code ✓ (bedo_entry) |
| 28 | The duration check, three passes | code | next: dusk_audit evidence pass |  |
| 29 | device | judgment | J2 | ambiguous ones listed by dusk_audit (next) |
| 30 | Containers | code ✓ | look-behind container test | the name is asked → J14 |
| 31 | action key | code ✓ | core/bedo_entry (format, only ⚡ rows) + core/bedo_reader |  |
| 32 | deliverable, and chat | judgment | J10 |  |
| 33 | be•do logs its own working sessions | judgment | J10 | time as the sum of stretches → code next (stretches) |
| 34 | Bucketing | judgment | J12 | active-only at the read → code next |
| 35 | DAWN (part header) | drop | — |  |
| 36 | Startup | code ✓ | core/bedo_preflight emits the chat-name line first |  |
| 37 | The suggested morning flow | facts | catalog order, read live |  |
| 38 | The steps | judgment | J8 | order lives in the catalog |
| 39 | The look ahead | code ✓ | bedo-day-ahead |  |
| 40 | It builds The Day Ahead, unasked | code ✓ | bedo-day-ahead + its loader |  |
| 41 | The Pareto three | code ✓ | bedo-day-ahead | uncalendared-first and dedupe by subject → next (A213) |
| 42 | Media and queue filtered at the read | code ✓ | bedo-day-ahead filtered_open | 📼 video now counts as media (facts.json) |
| 43 | The calendar, three calendars, two horizons | code ✓ | bedo-day-ahead bedo_cal | prep drafted for her okay → J8 |
| 44 | The rest: the quick-sweep strip | drop | her yes 3 (accepted) | meeting prep still fires from the event |
| 45 | DAY (part header) | drop | — |  |
| 46 | Capture as it happens | judgment | J2 | capture stretches → code next |
| 47 | My day finishes the working chats' rows | code ✓ | core/bedo_dusk_audit: filtered read, attention derived, for-my-day lists named | attention derived, not asked |
| 48 | Usage readings | drop | her yes 4 (accepted) |  |
| 49 | Journal, uninstrumented | judgment | J2 |  |
| 50 | Glimmer | judgment | J2, J6 |  |
| 51 | Area of inquiry | judgment | J12 | now queueable (A246) |
| 52 | Clear gmail inbox | judgment | J16 (clear-inbox skill) |  |
| 53 | Calendar | code ✓ | look-behind calendar_sync |  |
| 54 | Photos | code | next: an EXIF helper that opens the sub-IFD | datetime precedence → J2 |
| 55 | DUSK (part header) | drop | — |  |
| 56 | The evening: three enforcement targets | facts | facts.json self_check |  |
| 57 | The map check emits rows | judgment | J8 | matching existing rows → dusk_audit next |
| 58 | The one-pass list | code ✓ | core/bedo_dusk_audit |  |
| 59 | The gate | code ✓ | core/bedo_dusk_audit gate, through bedo_remaining (catalog against the day) |  |
| 60 | The quest | judgment | J13 | points and payout stay in the quest data row |
| 61 | Quest details, one line per mini-quest | judgment | J13 |  |
| 62 | The quest scores zero on the wheel | code ✓ | look-behind wheel |  |
| 63 | Screen time | judgment | J16 (its spec) |  |
| 64 | Friends-are-here days | judgment | J13 |  |
| 65 | The daily flag | code ✓ | core/bedo_dusk_audit flag |  |
| 66 | SUNDAY (part header) | drop | — |  |
| 67 | my week is one long chat | judgment | J11 |  |
| 68 | QA check, the weekly self-check | code ✓ | close.py check; thresholds in facts.json | depth dropped (her yes 1); the people pool is now defined (contact rows with a person) |
| 69 | The sequence | judgment | J11 | the mechanical half is close.py |
| 70 | The three-and-three is a row | judgment | J11 | the row no longer takes an action key (only ⚡ rows do) |
| 71 | The one-word intention | judgment | J9 |  |
| 72 | Drives and rhythms reviewed | judgment | J11 |  |
| 73 | One bucket of backlog triage | drop | her yes 2 (accepted) |  |
| 74 | The two mechanisms that age work out | judgment | J12 | plus quickie |
| 75 | The monthly ahead-review | code ✓ | bedo-ahead-review | reads every base, live first, now |
| 76 | The weekly export | code ✓ | close.py export + core/bedo_export |  |
| 77 | The handoff doc | judgment | J11 |  |
| 78 | The split | code ✓ | core/bedo_split + close.py plan, verify | the clone stays hers |
| 79 | Past-week lookback | code ✓ | core/bedo_reader (I14, I15) | calendar first → J3 |
| 80 | A closed week's CSV is the archive | code | next: archive reader applying the corrections file |  |
| 81 | REFERENCE (part header) | drop | — |  |
| 82 | The bases, the code, what ships | facts | facts_local.json |  |
| 83 | One table, one base | facts | facts_local.json bases |  |
| 84 | The code lives in the project files | drop | — | plumbing: the repo is public and the loaders clone it |
| 85 | GitHub runs, Drive records | judgment | J15 |  |
| 86 | Drive copies | judgment | J15 |  |
| 87 | The four layers | drop | — | plumbing: V53's own shape (core · facts · facts_local · judgment) replaces it |
| 88 | The pages | code ✓ | the builders |  |
| 89 | One living page per window | judgment | J15 | the page links are hers (facts_local) |
| 90 | Pages render on demand; a trigger files the final | code | next: the scheduled trigger |  |
| 91 | The readings | code ✓ | look-behind readings | footing → J8; the ring dropped (her yes 5) |
| 92 | The wheel | code ✓ | look-behind |  |
| 93 | The balance bar | code ✓ | look-behind |  |
| 94 | The day behind, shape | code ✓ | look-behind |  |
| 95 | The day, entry by entry | code ✓ | look-behind |  |
| 96 | How the day went | code ✓ | look-behind |  |
| 97 | What moved reads a real span | code ✓ | look-behind |  |
| 98 | Page conventions | code ✓ | the page engines |  |
| 99 | Rhythms, drives and destinations | judgment | J12 |  |
| 100 | The five types | facts | facts.json rhythm_types |  |
| 101 | destination is a drive field | judgment | J12 |  |
| 102 | feeds | judgment | J12 |  |
| 103 | Codes | judgment | J12 |  |
| 104 | Milestone | judgment | J12 | always names its drive → code ✓ (bedo_entry) |
| 105 | The queues | judgment | J12 |  |
| 106 | Four catalogs, one shape | facts | facts.json catalog_standings |  |
| 107 | Stories | judgment | J12 |  |
| 108 | Started media | judgment | J12 |  |
| 109 | Recipes | judgment | J16 (provisions skill) |  |
| 110 | Supplies | judgment | J12, J16 |  |
| 111 | The shopping watch | judgment | J16 (shopping-watch skill) |  |
| 112 | Chats | judgment | J10 |  |
| 113 | Three kinds of chat | judgment | J10 |  |
| 114 | The first reply infers the kind | judgment | J10 |  |
| 115 | Model and effort at the open | judgment | J10, J15 |  |
| 116 | Titles | facts | facts.json chat_status; the chat-title skill |  |
| 117 | D6's spine, the five phases | drop | — | project state; lives in the stream as action rows |
| 118 | Amendments | judgment | J0 |  |
| 119 | The fold, and the archive | drop | — | plumbing: an amendment now lands in code, facts or judgment by pull request |
| 120 | Operations reference (part header) | drop | — |  |
| 121 | Airtable patterns | code ✓ | core/bedo_reader; facts.json airtable |  |
| 122 | The token budget | drop | her yes 4 (accepted) | the model dials → J15 |
| 123 | The budget page | drop | her yes 4 (accepted) |  |
| 124 | Efficiency and model choice | judgment | J15 |  |
| 125 | The skills | drop | — | plumbing: each skill carries its own text (J16) |
| 126 | The code | drop | — | plumbing: the repo README lists it |

## Active amendments

| A# | date | what it says | place | where |
|---|---|---|---|---|
| A1 | 08-15 | a one-week calibration of practice timing; bands were set from it and timing stopped | drop · superseded | — |
| A2 | 08-18 | what the morning and evening Oura practices each carry | facts | catalog notes |
| A3 | 08-18 | an evening photo sweep: meals and workouts from images, not memory | judgment | J2 |
| A4 | 08-18 | the daily export as the last dusk step | drop · superseded | V52 dusk: no day summary, no export |
| A5 | 08-18 | today's calendar events written as rows at dawn | code ✓ | day-ahead |
| A6 | 08-19 | account for the 24 hours: measured, scheduled, derived, unaccounted | code ✓ | look-behind (how the day went) |
| A7 | 08-19 | the week's all-days view is a section of the Sunday page | code | next: week-behind builder |
| A8 | 08-19 | the chat-name line is the first line of the first reply | code ✓ | core/bedo_preflight emits the chat-name line |
| A9 | 08-19 | catch the small things: balance simplicity and granularity | judgment | J1 |
| A10 | 08-19 | an older three-calendar scope | drop · superseded | by the three-calendars amendment (V52) |
| A11 | 08-19 | name the time left before an event within the hour, once | judgment | J8 |
| A12 | 08-19 | a fourth guiding light | drop · superseded | values live in the rhythms base |
| A13 | 08-19 | guiding-light candidates left open | drop · superseded | values live in the rhythms base |
| A14 | 08-19 | a per-day chat envelope row | drop · superseded | J10 session entries, stretches |
| A15 | 08-20 | the look ahead page, sorted by leverage | code ✓ | day-ahead |
| A16 | 08-20 | undated means two things; the queue box separates them | judgment | J12 |
| A17 | 08-20 | deliverables named date-first, no emoji | judgment | J15 |
| A18 | 08-20 | the daily review as the last dusk step | drop · superseded | look-behind step + midnight trigger |
| A19 | 08-20 | every deliverable files into the week folder that made it | judgment | J15 |
| A20 | 08-20 | neutral could not be recorded | drop · superseded | ⚪ neutral now exists (facts.json) |
| A21 | 08-20 | the emotion field holds the five colours; the word is its own field | facts | facts.json emotion |
| A22 | 08-20 | triage runs in batches on a built page, recommendation written | code ✓ | ahead-review deck |
| A23 | 08-21 | a horizon type | drop · superseded | facts.json rhythm_types |
| A24 | 08-21 | open-ended drives: a real end on no schedule | judgment | J12 |
| A25 | 08-21 | labels are lowercase | code ✓ | page engines |
| A26 | 08-22 | a calendar search reads every calendar before saying no | judgment | J3 |
| A27 | 08-22 | a rhythm retired and replaced | drop · superseded | rhythms base data |
| A28 | 08-22 | before scoring the quest, read his rows first; ask only gaps | judgment | J13 |
| A29 | 08-22 | trail language for the types | drop · superseded | facts.json rhythm_types |
| A30 | 08-22 | the map check gives a done calendar event its real span | judgment | J8 |
| A31 | 08-22 | avoid the word never in page copy and voice | judgment | J4 |
| A32 | 08-22 | interests are read from area-of-inquiry rows, not declared | judgment | J12 |
| A33 | 08-22 | an older review and look-ahead page shape | drop · superseded | look-behind page shape (V52) |
| A34 | 08-22 | the dawn flow closes itself on its last practice | judgment | J8 |
| A35 | 08-22 | batch triage cadence: monthly and seasonal (weekly part: dropped, her yes 2) | judgment | J11 |
| A36 | 08-23 | the ten mini-quests, in full | facts | the quest data row (read nightly; never archived) |
| A37 | 08-31 | preflight reads the handoff first | code ✓ | core/bedo_preflight --handoff: must name the same base |
| A38 | 09-01 | the flow list as a code block | drop · superseded | by the remaining-list widget (A248) |
| A39 | 09-01 | future-blessings gratitude is a reserved trigger, not a flow step | facts | catalog |
| A40 | 09-01 | a monthly intention word beside the weekly one | drop | her yes 5 (accepted) |
| A41 | 09-01 | shows and movies are never reminders | code ✓ | day-ahead (filtered at the read) |
| A42 | 09-01 | the circle palette carries no hue; colour means feeling | code ✓ | page engines |
| A43 | 09-01 | the week river: one lane a day | code | next: week-behind builder |
| A44 | 09-01 | weekly sociogram views off | code | next: week-behind builder |
| A45 | 09-01 | weekly memorable cards | code | next: week-behind builder |
| A46 | 09-01 | a dropped weekly panel | drop · superseded | week-behind shape |
| A47 | 09-01 | queries through Airtable, bulk through files | code ✓ | core/bedo_reader (reads dumps on disk) |
| A48 | 09-01 | the three-and-three belong to the week under review | code | next: week-behind builder |
| A49 | 09-01 | closeness is interaction; co-presence is a halo | code ✓ | look-behind (who was in your day reads person only) |
| A50 | 09-01 | a practice added mid-week is marked new, never scored 0/7 | code | next: close.py check |
| A51 | 09-01 | every day on the weekly opens with a lead | code | next: week-behind builder |
| A52 | 09-01 | a long row with no feeling as a capture gap | drop | her yes 1 (accepted) |
| A53 | 09-01 | a row naming only someone else is read as theirs | code ✓ | look-behind |
| A54 | 09-01 | the day lead says what she did | judgment | J5 |
| A55 | 09-01 | at most four memorable cards a day | code | next: week-behind builder |
| A56 | 09-01 | the day lead names what she did; the place is a footnote | judgment | J5 |
| A57 | 09-01 | two good and two hard cards a day | code | next: week-behind builder |
| A58 | 09-01 | one labelled line of be•do prose per day on the weekly | judgment | J4 |
| A59 | 09-01 | cards carry her words, not just the title | code ✓ | look-behind (entries carry her words) |
| A60 | 09-01 | what counts toward one mini-quest | judgment | J13 |
| A61 | 09-02 | per diem tracked from receipts | drop | her yes 5 (accepted) |
| A62 | 09-02 | does-it-exist is a filtered search, never a paged list | judgment | J3 |
| A63 | 09-02 | surface his open mini-quests during the day | judgment | J13 |
| A64 | 09-02 | one household ask, two rows | judgment | J13 |
| A65 | 09-02 | a QA sweep that fixes what it can and names at most three | code | next: dusk_audit |
| A66 | 09-02 | mechanical reconciliations settled by be•do, stated in a line | judgment | J4 |
| A67 | 09-02 | every action offers its feeling at close | drop | her yes 1 (accepted) |
| A68 | 09-02 | durations resolve from instruments before anything is asked | code | next: dusk_audit (evidence pass) |
| A69 | 09-02 | the self-check reports what the build read | code ✓ | look-behind self-check |
| A70 | 09-02 | the wheel says why it is that shape | code ✓ | look-behind wheel |
| A71 | 09-02 | a deduped row takes ✖️ in status, named as a dedupe | judgment | J12 |
| A72 | 09-02 | the daily sociogram views off | code ✓ | look-behind |
| A73 | 09-02 | an oversized read lands on disk | code ✓ | core/bedo_reader |
| A74 | 09-02 | intentions and the action check lead the daily page | code ✓ | look-behind (follow-through) |
| A75 | 09-03 | a truncated template download | drop · superseded | templates retired |
| A76 | 09-03 | the wheel lists every row behind a petal | code ✓ | look-behind wheel |
| A77 | 09-03 | still open honours the key chain and the queue box | code ✓ | core/bedo_reader (chain heads) |
| A78 | 09-03 | a practice that opens with ⚡ is not an ⚡ action | code ✓ | core/bedo_entry (exact practice match) |
| A79 | 09-03 | a panel for the deliberately dateless | code | next: queues page |
| A80 | 09-03 | a transcription trap | facts | facts_local (her transcription traps) |
| A81 | 09-03 | the wheel names only what rose; the flow becomes a strip | code ✓ | look-behind wheel |
| A82 | 09-03 | build the daily first; the weekly once, at the end | judgment | J15 |
| A83 | 09-03 | the chat clock drifts; re-read it before writing (I12) | code ✓ | core/bedo_preflight clock: the machine's, offset checked against the zone |
| A84 | 09-04 | a late close costs more; capture rows written unasked each stretch | judgment | J10 |
| A85 | 09-04 | a ninth status for a window that closed | drop · superseded | facts.json status (eight) |
| A86 | 09-04 | what the reading and training mini-quests mean | judgment | J13 |
| A87 | 09-04 | dusk flow cleanup: meds out, supplements in | facts | catalog |
| A88 | 09-05 | provisions: one table for what is had and wanted | judgment | J16 (provisions skill) |
| A89 | 09-05 | meal ideas scored only when she asks | judgment | J16 (provisions skill) |
| A90 | 09-05 | known traps corrected silently, new ones flagged | judgment | J5 |
| A91 | 09-05 | meal prep is its own row when she cooks | judgment | J2 |
| A92 | 09-05 | the week's dinner shape and the provisions page | judgment | J16 (provisions skill) |
| A93 | 09-05 | a container is never an ⚡ action | code ✓ | look-behind container test |
| A94 | 09-05 | the daily is too wordy; context-dependent quotes stay off | code ✓ | look-behind (entries cut at ~240) |
| A95 | 09-06 | a rewritten cosmology | drop · superseded | J1 and the rhythms types |
| A96 | 09-06 | rhythms as cadence; weather, terrain, feeling | drop · superseded | J1 |
| A97 | 09-06 | the kid's highlight retired | drop · superseded | V52 keeps the kid's highlight practice |
| A98 | 09-06 | drive versus destination; codes are a series | judgment | J12 |
| A99 | 09-06 | guides as a fourth layer | drop · superseded | facts.json rhythm_types (value) |
| A100 | 09-06 | be•do's purposes serve a more meaningful life | judgment | J1 |
| A101 | 09-07 | everything is a drive; projects are not a category | judgment | J12 |
| A102 | 09-07 | one week of her offering the headline | drop · superseded | — |
| A103 | 09-07 | a headline every day | code ✓ | look-behind |
| A104 | 09-07 | wind renamed air; a key to the eight | facts | facts.json wellness |
| A105 | 09-07 | status precedence as a labelled fallback for old CSVs | code | next: archive reader (CSV + corrections) |
| A106 | 09-07 | balance replaces roundness | code ✓ | look-behind |
| A107 | 09-07 | the promote checkbox | drop | her yes 5 (accepted) |
| A108 | 09-07 | what survives a weekly project change | drop · superseded | repo + Drive (J15) |
| A109 | 09-07 | the eight go lowercase | facts | facts.json wellness |
| A110 | 09-07 | rhythm tagging is tighter | judgment | J12 |
| A111 | 09-07 | one highlight a day (promote part: dropped, her yes 5) | judgment | J2 |
| A112 | 09-08 | the quick-sweep strip skips queued rows | drop | her yes 3 (accepted) |
| A113 | 09-08 | nudge her toward finishing what she starts | judgment | J1 |
| A114 | 09-08 | never mint an ⚡ row from a session entry's still open | judgment | J10 |
| A115 | 09-09 | stale ▶️ rows get resolved, not displayed | code ✓ | ahead-review deck |
| A116 | 09-09 | thought partner, not advisor, on her own ground | judgment | J4 |
| A117 | 09-09 | media is queue by definition | drop · superseded | stories base (J12) |
| A118 | 09-09 | a shopping watch on decided items only | judgment | J16 (shopping-watch skill) |
| A119 | 09-09 | resolve a bare yes by content, keep replies short | judgment | J4 |
| A120 | 09-09 | offer feeling words from the emotions table's definitions | judgment | J6 |
| A121 | 09-10 | the flow list prints every turn | drop · superseded | by the widget (A248) |
| A122 | 09-10 | work events be•do puts on the calendar open with the project glyph | judgment | J15 |
| A123 | 09-10 | a private repo per actively worked drive | judgment | J15 |
| A124 | 09-11 | the flow list prints after a flow practice | drop · superseded | by the widget (A248) |
| A125 | 09-11 | never ask about media | judgment | J12 |
| A126 | 09-11 | the dawn flow closes at noon, unasked | code | next: backup close names what it missed |
| A127 | 09-11 | the flow list is read, never recalled | code ✓ | core/bedo_remaining (live catalog read) |
| A128 | 09-11 | the evening blessing's fixed words | facts | catalog note |
| A129 | 09-12 | an inbox sweep every evening | judgment | J16 (clear-inbox skill) |
| A130 | 09-13 | Sunday's reflective half opens the day | judgment | J11 |
| A131 | 09-13 | the sociogram draws interactions, not mentions | code ✓ | look-behind |
| A132 | 09-13 | a practice carries a cadence | facts | catalog CADENCE: line |
| A133 | 09-13 | a closing row carries the time of the act | judgment | J2 |
| A134 | 09-13 | tending, and the day's growth read thin · steady · wide | code ✓ | look-behind readings |
| A135 | 09-13 | a growth checkbox | drop · superseded | growth is read seasonally (V52) |
| A136 | 09-13 | contracted · maintained · expanded with a floor | drop · superseded | the floor is dropped (V52) |
| A137 | 09-13 | promote proposed from her words | drop | her yes 5 (accepted) |
| A138 | 09-13 | two rhythms merged | drop · superseded | rhythms base data |
| A139 | 09-13 | an action shows as one line per key | code ✓ | core/bedo_reader + builders |
| A140 | 09-13 | the full row list; the flow panel is capture | code ✓ | look-behind |
| A141 | 09-13 | a look behind read in one minute | code ✓ | look-behind |
| A142 | 09-13 | solo fortress on evidence (narrowed by A210) | judgment | J13 |
| A143 | 09-13 | every look behind names what it can't see | code ✓ | look-behind self-check |
| A144 | 09-13 | what the work moved, with measured time | code ✓ | look-behind |
| A145 | 09-13 | a queue row is never stuck or overdue | code ✓ | day-ahead and ahead-review filters |
| A146 | 09-13 | closed actions nest their chain | code ✓ | look-behind |
| A147 | 09-13 | a late close leaves the new week's first days behind | code ✓ | core/bedo_split (reads the outgoing base) |
| A148 | 09-13 | drives and rhythms reviewed inside the close | judgment | J11 |
| A149 | 09-13 | the dusk close waits until the day is complete | code ✓ | core/bedo_dusk_audit gate |
| A150 | 09-14 | rules only; week state lives in the bases and handoff | judgment | J0 |
| A151 | 09-14 | quest details carry the observed time | judgment | J13 |
| A152 | 09-14 | the screen layer on the quest | judgment | J16 (screen-time spec) |
| A153 | 09-14 | every builder lives in the project files | drop · superseded | the public repo + loaders |
| A154 | 09-15 | media and queued rows filtered out at the read | code ✓ | day-ahead (filtered at the read) |
| A155 | 09-15 | friends-here days run loose; 9 PM holds | judgment | J13 |
| A156 | 09-15 | one codebase across window and direction | code ✓ | the builders |
| A157 | 09-15 | bucket candidates from active rhythms only | code | next: rhythms read filtered to active |
| A158 | 09-15 | be•do's design principles | judgment | J1 |
| A159 | 09-15 | codes renumbered every 1 January | judgment | J12 |
| A160 | 09-16 | the remaining list inside the Entry Check | drop · superseded | by the widget (A248) |
| A161 | 09-16 | started media held quietly | judgment | J12 |
| A162 | 09-17 | the rhythm types the base carries | facts | facts.json rhythm_types |
| A163 | 09-17 | a milestone records a real step toward a destination | judgment | J12 |
| A164 | 09-17 | the look ahead reads two weeks of calendar | code ✓ | day-ahead (bedo_cal) |
| A165 | 09-18 | gratitude is bulleted | code ✓ | core/bedo_entry (gratitude check) |
| A166 | 09-18 | the flow list prints remaining practices only | code ✓ | core/bedo_remaining (remainders, done count on top) |
| A167 | 09-18 | the Pareto three are not her intentions | code ✓ | day-ahead |
| A168 | 09-18 | her son's rows bucket like hers | judgment | J12 |
| A169 | 09-18 | dedupe by record id, live base first (I15) | code ✓ | core/bedo_reader (merge_live_first) |
| A170 | 09-18 | the quest row scores zero on the wheel | code ✓ | look-behind wheel |
| A171 | 09-18 | clear-inbox replaces the email import rules | judgment | J16 (clear-inbox skill) |
| A172 | 09-18 | whose day a row is in is derived | code | next: his day page |
| A173 | 09-18 | recipes, a permanent base | facts | facts_local bases |
| A174 | 09-18 | a want is a supplies row; the deciding is an action | judgment | J12 |
| A175 | 09-18 | three queues; impulse media never queued | facts | facts.json never_queued |
| A176 | 09-18 | clear-inbox ticks the queue box on reading rows | drop · superseded | stories standing (J12) |
| A177 | 09-18 | every session entry links its chat | judgment | J10 (session-entry skill) |
| A178 | 09-18 | the inbox sweep is a time window; it archives unasked | judgment | J16 (clear-inbox skill) |
| A179 | 09-18 | chat titles carry code and step | judgment | J10 (chat-title skill) |
| A180 | 09-19 | growth inner, effectiveness outer; the ring per phase | code ✓ | look-behind readings (ring part: dropped, her yes 5) |
| A181 | 09-19 | the floor is dropped | code ✓ | look-behind readings |
| A182 | 09-19 | every row carries a device, deduced | judgment | J2 |
| A183 | 09-19 | the inbox practice's name | facts | catalog |
| A184 | 09-19 | whoever is doing it owns the row | judgment | J7 |
| A185 | 09-19 | three kinds of chat | judgment | J10 |
| A186 | 09-19 | imported rows lead with what she can do | judgment | J16 (clear-inbox skill) |
| A187 | 09-19 | the daily checks are balance and effectiveness | code ✓ | look-behind readings |
| A188 | 09-19 | footing gates effectiveness | judgment | J8 |
| A189 | 09-19 | effectiveness is drive work feeding a destination | code ✓ | look-behind readings |
| A190 | 09-19 | the five types | facts | facts.json rhythm_types |
| A191 | 09-19 | the day pie's drawing rules | drop · superseded | how the day went (V52) |
| A192 | 09-19 | be•do's mark in chat titles | facts | facts.json glyph_codepoints |
| A193 | 09-19 | drives point at destinations through their own field | judgment | J12 |
| A194 | 09-19 | every document a chat makes gets a Drive copy | judgment | J15 |
| A195 | 09-19 | a rhythm carries no destination | judgment | J12 |
| A196 | 09-19 | the inbox ends empty | judgment | J16 (clear-inbox skill) |
| A197 | 09-19 | coherence; nothing has to converge | judgment | J1 |
| A198 | 09-19 | home-alarm alerts get no row | judgment | J16 (clear-inbox skill) |
| A199 | 09-27 | the handoff goes to both week folders | judgment | J11 |
| A200 | 09-28 | the morning mantra prints by name | code ✓ | core/bedo_remaining (names only) |
| A201 | 09-28 | a utility or bank notice is read in the body | judgment | J16 (clear-inbox skill) |
| A202 | 09-28 | a session entry is checked by key and status | judgment | J10 (session-entry skill) |
| A203 | 09-28 | Fable is no longer avoided | judgment | J15 |
| A204 | 09-28 | a row goes in the base of its own week | code ✓ | core/bedo_entry (base for a row's own week) |
| A205 | 09-28 | a scheduled look behind drafts an editable lead and story | code ✓ | look-behind words.py |
| A206 | 09-28 | the day ahead's calendars come through the connector | code ✓ | day-ahead bedo_cal |
| A207 | 09-29 | builder edit is hers to say, be•do's to classify | judgment | J10 |
| A208 | 09-29 | the remaining list prints bare names | code ✓ | core/bedo_remaining (bare names) |
| A209 | 09-29 | secure is assumed; recovery mode is her word | judgment | J8 |
| A210 | 09-29 | the family bed is the default | judgment | J13 |
| A211 | 09-29 | footing is the status's name | judgment | J8 |
| A212 | 09-29 | on a low day, offer her chosen prayer by pointer | judgment | J8 |
| A213 | 09-29 | the three come from uncalendared work, deduped by subject | code | next: day-ahead picks |
| A214 | 09-29 | the nightly pair of pills, two rows | facts | catalog notes |
| A215 | 09-29 | hero's service is him asking | judgment | J13 |
| A216 | 09-29 | the dusk tail order | facts | catalog order |
| A217 | 09-29 | a milestone always names its drive | code ✓ | core/bedo_entry (milestone check) |
| A218 | 09-30 | prompt for feeling with candidate words | judgment | J6 |
| A219 | 09-30 | a rule a turn must remember moves into a mechanism | code ✓ | core/bedo_preflight; the principle is J0 |
| A220 | 09-30 | the sweep filters on the message's own time | judgment | J16 (clear-inbox skill) |
| A221 | 10-01 | a pet moment leads with the animal's name | judgment | J5 |
| A222 | 10-01 | secure base is not a daily practice | facts | catalog (secure base inactive) |
| A223 | 10-01 | the provisions shelf is probably wrong | judgment | J12 |
| A224 | 10-01 | a bolded core on the remaining list | drop · superseded | by the widget spec (A237) |
| A225 | 10-01 | a labelled thread with no row is imported | judgment | J16 (clear-inbox skill) |
| A226 | 10-02 | the readiness mark at 85 or above | facts | facts.json readiness_mark_at_or_above |
| A227 | 10-02 | the mantra by name only | code ✓ | core/bedo_remaining (names only) |
| A228 | 10-02 | a core, with the rest on one line | code ✓ | core/bedo_remaining (core block, the rest on one line; core in facts.json) |
| A229 | 10-02 | the dawn movement block follows morning sun | facts | catalog order |
| A230 | 10-02 | flows are windows | judgment | J8 |
| A231 | 10-02 | QA corrections go onto the rows the same night | judgment | J8 |
| A232 | 10-02 | time spent counts as the row's length | code ✓ | look-behind spans() |
| A233 | 10-02 | a place is not an activity | code ✓ | look-behind qa.unexplained |
| A234 | 10-02 | a moment takes its practice's usual length | code ✓ | look-behind (usual length) |
| A235 | 10-02 | rules she has settled go into code | judgment | J0 |
| A236 | 10-02 | the build order (this migration first) | drop · state | lives in the stream as an action row |
| A237 | 10-02 | the pill strip spec | code ✓ | core/bedo_remaining --widget, the predicted order (bedo_order) and the sunrise hold |
| A238 | 10-02 | an unused intention slot is not drawn | code | next: day-ahead engine |
| A239 | 10-02 | an intention carries a when and why, not a date | judgment | J9 |
| A240 | 10-02 | noticing, offered at the dawn close | judgment | J8 |
| A241 | 10-02 | unexplained stretches filled from clues, marked estimated | judgment | J16 (look-behind skill QA step) |
| A242 | 10-02 | ⏯️ handed off | facts | facts.json chat_status |
| A243 | 10-02 | queue rows offered when she has time | judgment | J8 |
| A244 | 10-02 | the monthly review: ⬜ and ▶️, five glyphs, no dates | code ✓ | ahead-review build (scope) |
| A245 | 10-02 | places, the ninth permanent base | facts | facts_local bases |
| A246 | 10-02 | areas of interest may be queued | judgment | J12 |
| A247 | 10-02 | resolve a chain across every base before a review or patch | code ✓ | core/bedo_reader + ahead-review (every base, live first) |
| A248 | 10-03 | the widget is the remaining list | code ✓ | core/bedo_remaining --widget, run by bedo-checks; J8 says it ends every reply |
| A249 | 10-03 | read the feeling from her words | judgment | J6 |
| A250 | 10-03 | the dusk close audits rows; chat time is the sum of stretches | code ✓ | core/bedo_dusk_audit (the five checks) + core/bedo_stretches |
| A251 | 10-03 | a window chat's ⚡ row has no duration and no drive | code | next: session entry check |
| A252 | 10-03 | capture scores zero on the wheel | code ✓ | look-behind wheel |
| A253 | 10-03 | overlap counts once; logging is tending | code ✓ | look-behind wheel and bar |
| A254 | 10-03 | chat-title status glyphs; the objective is a check | facts | facts.json chat_status (+ J10 objective) |
| A255 | 10-03 | quickie: the word and its tests | judgment | J12 |
| A256 | 10-03 | be•do may mark a quickie, shown first | judgment | J12 |
| A257 | 10-03 | quickie has its own checkbox | facts | facts_local stream_fields.quickie |
| A258 | 10-03 | page rows link their Drive copy into the viewer (link stays local) | judgment | J15 |
| A259 | 10-03 | my day's objective: see each flow to its close | judgment | J8 |
| A260 | 10-04 | my day opens the dusk flow after about 7 PM | judgment | J8 |
| A261 | 10-04 | one piece of evidence logs every practice it shows | judgment | J2 |
| A262 | 10-04 | the dusk one-pass list comes from a filtered read | code ✓ | core/bedo_dusk_audit (filtered read) |
| A263 | 10-04 | the weekly base pointer | drop · state | resolved by name each run (facts_local weekly_name) |

## Not folded yet

No amendment row is marked folded or archived. When she has read V53 and says it is faithful, every row above moves to `code/amendments-folded-archive.md` and is marked folded — except the quest's data row (A36), which the scorer reads every night.
