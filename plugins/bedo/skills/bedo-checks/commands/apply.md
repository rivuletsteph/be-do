# `apply`

**When:** every stream write from a session that can run code

**Command:** `apply ops.json [--base "w48 be•do"] [--chat MMDD] [--dry]`

**Rows are written by code, never retyped by a model** (24 Nov 2026, her words: in a way that conserves tokens). On 23 Nov a day's Code steps spent most of their tokens sending rows through the model by hand, a whole details field typed back to add one line to it. Write a short file of what changes, in the names `entry` reads, and let `apply` do the rest:

```
[{"title": "…", "practice": "📝 log", "status": "● log", "datetime": "…Z"},       a new row
 {"id": "rec…", "status": "✅ done"},                                             a change: only what changes
 {"id": "rec…", "append": "[be•do] one more line"},                               added at the end of its details
 {"id": "rec…", "her_words": "What she said. (Mon 23 Nov, 9:00p)"}]               added above the divider
```

It reads each row it adds a line to, so the text already there is carried forward verbatim, by code. A new row goes through the entry check; what the check deduces by itself (a device, a person, a wellness, an end) is filled in and checked again; a row left with a `FIX` is not written and is named, so fix its line in the file and run it again with only that row. `--dry` checks and writes nothing.

**Where the credential may write, it writes**, and prints one line. **Where it may only read** (a cloud session's saved secret, J10) it says so and saves the same writes, in field ids, as `connector.json` beside the file: send `create` and `update` through the connector as they are, typecast off, fifty a call. Never rebuild them by hand.

A plan another check prints as `--json` (the ring read's plan, the braid's patches and new rows, the map check's rows) goes into the file as it is; only what a model had to read (a photo, her words) is typed.
