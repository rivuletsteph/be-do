# quest-day — the child's daily quest page

The page a parent hands to the child: the day's score out of ten and its money, the day's big win as a
trophy photo, the five realms with two mini-quests each, and the week line. Settled 2 Nov 2026 as the
standing format (her words: I love this format, please save this artifact format; it works so well).
It is built **at the dusk wrap-up** and linked on the my day page (her word, 8 Nov 2026), and gone over the next morning (her word, 4 Nov 2026: go over it
every morning and go over it with him when he's rested — here's what went great yesterday, here's where you missed out — so he
can correct it; in time it grows into planning). It publishes to one living page (`quest_url` in her settings), and the
morning chat's preflight hands her the link. She can still ask for a day by hand, with photos.

Rules the page keeps:
- **Written to the child**, second person, in his register. A missed quest is a *next time* line, never a mark against him.
- **Points are counted from the quests**, not typed: each ✓ is a point, `per_point` dollars each (default 0.50, so ten points is $5.00).
- **Photos are few**: one trophy photo for the day's big win, and at most one beside a quest it proves. Images go in as small
  `data:` URIs (about 640 px on the long side), so the page stands alone.
- **Nothing personal lives here.** The name, the day, the lines and the photos come from the day's ⚔️ quest row and its photos
  at build time; this folder holds only the shape.

Build it with one command, from the day's ⚔️ quest row (its scored lines, `· ✓ Quest — what he did`):

```
python3 plugins/bedo/assets/quest-day/quest_page.py --row quest_row.json --name NAME --day "Sunday · 1 November" \
    --trophy big_win.jpg --trophy-text "Today's big one: …" [--photo "The Fuel=snack.jpg"] --out quest.html
```

It turns each line to him (he → you, mechanically: read every line before she sees it), takes her notes out (*her word*),
gives a missed quest with nothing said its next-time line, and counts the points.

The morning routine's way finds the day's ⚔️ row in the stream dumps and writes the week line itself
(`Day 3 of this week's quest: 18 points so far, $9.00`); exit 4 means no scored row that day:

```
python3 plugins/bedo/assets/quest-day/quest_page.py --from-stream data/w45.json --date 2026-11-03 \
    --local look_behind_local.json --name NAME --out quest.html [--row reworded.json]
```
Or by hand: replace `/*TITLE*/` with the page's name (`<Name>'s Quest · <Weekday>`) and `/*DATA*/` with JSON:

```json
{"name": "…", "day": "Sunday · 1 November", "per_point": 0.5,
 "trophy": {"img": "data:image/jpeg;base64,…", "alt": "…", "text": "Today's big one: …"},
 "realms": [{"name": "🔆 Super Vitality", "quests": [
   {"name": "The Adventure", "won": true, "line": "…"},
   {"name": "The Fuel", "won": true, "line": "…", "img": "data:…", "alt": "…"}]}],
 "foot": "Day 1 of this week's quest. Payday is next Sunday."}
```

Order the realms with the wins first when that reads better for him; the realm and quest names follow the ten in the quest's data row.
