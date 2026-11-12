# flow-parts — the pieces the be•do pages share

Her word, 10 Nov 2026, asking for the my week page: *same look, same parts, made
for a whole week* — and *build from its components, never by borrowing its
stylesheet*. This folder is those components.

The my day page (`bedo-day-ahead`) and the my week page (`bedo-week-ahead`) are
different pages. A day has hours; a week has days. But they are the same page
furniture, and that furniture lives here in one copy, so the two cannot drift
apart: change a colour or a glyph here and it lands on both pages at the next
build.

| part | what it is |
|---|---|
| `theme.js` | light or dark, one button. Opens as the device is set; the button flips it for this look |
| `shell.css` | the ground, the chip, the theme button, the heading, the card |
| `blocks.css` | a rhythm block and a step on it — the my day page's rhythms-with-drives, the my week page's possible paths |
| `basics.js` | the theme button's icons and wiring, the chip, the heading, and the helpers the drawing code is written in |
| `kinds.js` | the kinds of time and their colours (her family of hues, 6 Nov 2026), plus Google's eleven for an event still ahead |
| `wellness.js` | the eight elements, their wheel colours and their line glyphs |
| `clock.js` | a time ends in a lowercase a or p — her amendment of 9 Nov 2026 |
| `baseflow-card.css` / `baseflow-card.js` | the base-flow river through seven mornings, and how one morning's number was made |
| `parts.py` | the loader both builders use, and the same a-or-p clock for Python |

The palette is **not** here. It is generated, not written: each build reads it
off a built day-ahead page's own `:root` and night block and injects it as
`/*ROOT*/` and `/*NIGHT*/` above these files, so both pages are literally the
same colours.

## How a page uses them

An engine marks where each part goes with a comment placeholder, the way the
base-flow widget was already marked:

```
/*THEMEJS*/  /*SHELLCSS*/  /*BLOCKSCSS*/  /*BASICSJS*/
/*KINDSJS*/  /*WELLNESSJS*/  /*CLOCKJS*/
/*BFCSS*/  /*BFJS*/  /*BFCARDCSS*/  /*BFCARDJS*/
```

and the builder calls `parts.fill(page)`, which replaces every placeholder the
page carries and leaves the rest alone. A page takes only the parts it uses.

`basics.js` expects `const D` (the page's own data) to be defined already, and
a `#chip` and `#h1` in the page. `baseflow-card.js` expects `#rv`, `esc()` from
`basics.js`, and `BedoBaseFlow` from `base-flow/base_flow.js`.

## Changing one

Change the file, not a page. Then run `tests/test_parts.py`: it fills both
engines and hands every `<script>` block to `node --check`, because a brace that
moves between files is invisible to a diff and fatal to a page.
