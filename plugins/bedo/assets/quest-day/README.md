# quest-day — the child's daily quest page

The page a parent hands to the child: the day's score out of ten and its money, the day's big win as a
trophy photo, the five realms with two mini-quests each, and the week line. Settled 2 Nov 2026 as the
standing format (her words: I love this format, please save this artifact format; it works so well).
It is built for the day before, while she looks back on it, and only when she asks for it (her cue: let's build the quest HTML), never unasked.

Rules the page keeps:
- **Written to the child**, second person, in his register. A missed quest is a *next time* line, never a mark against him.
- **Points are counted from the quests**, not typed: each ✓ is a point, `per_point` dollars each (default 0.50, so ten points is $5.00).
- **Photos are few**: one trophy photo for the day's big win, and at most one beside a quest it proves. Images go in as small
  `data:` URIs (about 640 px on the long side), so the page stands alone.
- **Nothing personal lives here.** The name, the day, the lines and the photos come from the day's ⚔️ quest row and its photos
  at build time; this folder holds only the shape.

Build: replace `/*TITLE*/` with the page's name (`<Name>'s Quest · <Weekday>`) and `/*DATA*/` with JSON:

```json
{"name": "…", "day": "Sunday · 1 November", "per_point": 0.5,
 "trophy": {"img": "data:image/jpeg;base64,…", "alt": "…", "text": "Today's big one: …"},
 "realms": [{"name": "🔆 Super Vitality", "quests": [
   {"name": "The Adventure", "won": true, "line": "…"},
   {"name": "The Fuel", "won": true, "line": "…", "img": "data:…", "alt": "…"}]}],
 "foot": "Day 1 of this week's quest. Payday is next Sunday."}
```

Order the realms with the wins first when that reads better for him; the realm and quest names follow the ten in the quest's data row.
