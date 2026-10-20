---
name: "bedo-photos"
description: "Sort the day's photos from the week folder's photos folder in Drive: read each file's time and place in code, drop duplicates, look only at what needs judgment, and sort with no decisions asked of the user (glimmer, highlight, important to the day, food, document, already logged). Plans stream rows and the day behind's photo strip, shows the plan, writes on her yes. Use at dusk unasked when the folder has new pictures, or when the user asks to sort, log or look at her photos."
---

# Photos into the day

The user's words, 20 Oct 2026: *I really want Claude to be able to
differentiate glimmers and highlights and important things about that day,
worth keeping, worth showing in the day behind. And then I want the food photos
and stuff to be documented, especially if there's something meaningful about
them, like where I was and all that. I don't want to have to make a bunch of
decisions.*

And: *I'd like to get to where the Google Photos album only holds actual photos
and Google Drive handles all the other things like screenshots* — and, in time,
the food photos too.

## Where the pictures are

She puts whatever be•do can use into the `photos` folder of the week's folder
in Drive (`be•do/<year>-W## <Mon D>/`; she may rename it, as `W43 photos`). On
the laptop that folder is in the local Drive sync, so the script reads it from
disk, with no connector calls. be•do cannot read her Google Photos library; the
share into Drive is the one step she keeps.

## Two passes: code, then eyes

**1. The script** (`scripts/photos.py`, no judgment):

```
python3 scripts/photos.py --dir "<week folder>/<photos folder>" --out <scratch>/photos-out \
  --date YYYY-MM-DD [--places <places.csv>]
```

It reads each file's time (EXIF, else the file name: `PXL_` names are UTC,
`Screenshot_` names are local) and lat/long. It drops byte-identical copies
(`x (1).jpg`), groups camera bursts and runs of screenshots, and writes 768-px
thumbnails and one contact sheet per run. `photos.json` lists everything.
`needs_look` is the short list to view. Pictures from other days are listed,
not dropped: they belong to that day's run.

**2. The look.** View only `needs_look`: the thumbnails, never the originals. A
contact sheet is one look for the whole run. Run this pass on Opus. The script
pass is cheap and can run on any model.

## Where she was

The camera's GPS when the file has it, named from `--places` (her places csv,
kept out of the repo). A picture shared from the phone's **Images** folder
keeps its location; one shared out of Google Photos arrives with it blanked
(tested 20 Oct 2026). When both copies of a picture are in the folder, the
script keeps the one with the location. With none, the next sources, in order,
are:

1. the day's stream rows around that time, such as a drive or an arrival;
2. her Timeline visits for that time;
3. a Timeline screenshot in the same folder.

Say which one was used.

## The sort: decided here, never asked

Each kept picture gets one sort. Read the day's stream first (one filtered
read). **A picture already behind a row is never logged twice.**

| sort | what it is | what happens |
|---|---|---|
| **already logged** | a row within ~10 min names it, or carries the photo checkbox for it | nothing new. If the camera time differs from the row's time (the row took the time it reached the chat), plan a time correction, carrying her words forward |
| **glimmer** | a small good moment: her people, light, nature, something tender | a `✨ glimmer` row, in her words if she said any, else a short plain title |
| **highlight** | the day's one best picture, from her camera, not a screenshot | first in the day behind's strip. A `⭐ highlight` row only if the day has none, marked *picked by be•do from her photos* |
| **important** | something that shapes the day: an award, an event, someone's news, her child's day | in the strip (up to five in all) and a `● log` row if the stream doesn't hold it yet |
| **food** | a meal or snack | a meal row by the time of day (breakfast · lunch · dinner · snack), titled by what it shows, with where she was and when. `bedo_meals` then places the minutes, as it does for any meal row |
| **document** | a receipt, a letter, a form, a page of text | kept in Drive. What it says goes on the row it belongs to. Never copy card numbers, auth codes or account numbers |
| **screenshot** | a screen she saved | read for what it says. Already used means nothing new. Something new means a row: `📲 capture` for an idea she saved, `● log` for news of her day. Screenshots never go in the strip |

Sorts are judgments from the picture and the day. When one is unclear, pick the
quieter sort and say so in the `[be•do]` block. Don't ask her.

## Show, then write

Before any stream write, show her the plan in one short list: each row (new or
changed), its time, its sort, and the picture it came from. Then the strip, in
order. Write on her yes, in one `create_records_for_table` call and one
`update_records_for_table` call (the bedo-airtable skill holds the ids). Every
row says in its `[be•do]` block *From her photo at H:MM* and where the place came
from. Rows from pictures carry the photo checkbox.

Then save the sort beside the pictures as `photos-YYYY-MM-DD.json`: file,
time, place and its source, sort, the row it went to, and the strip order. That
file is what the day behind will read for its photo strip.

Removing a duplicate copy from Drive needs her yes. Moving pictures out of her
Google Photos album is hers: say which ones can go (screenshots, documents,
food once logged).

## Not built yet

- **The day behind reads `photos-YYYY-MM-DD.json`** for its strip. The canon
  page already reserves up to five thumbnails.
- **Food in depth.** Her words, 20 Oct 2026: *a better more detailed nutrition
  workup on those food photos eventually, and link those to provisions and
  meal planning as well.*
- **The weekly close makes a `photos` folder** in each new week folder.

## Tests

`python3 tests/test_photos.py`: invented pictures cover the EXIF time and GPS
(south and west signs), the file-name times, an exact copy dropped, a burst and a
screenshot run grouped, a place matched within 150 m and not beyond, and another
day listed.
