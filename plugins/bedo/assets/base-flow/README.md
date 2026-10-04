# base flow

Where am I at, going into the day. In a river, base flow is the steady supply that keeps water running between storms. When it's low, the river only runs when something hits it. That's survival mode.

One number for the morning, made the way Oura makes readiness: three contributors carried from the day before, in equal thirds, each 0–100.

| contributor | what it reads |
|---|---|
| body | this morning's readiness. Nutrition from the day before will fold in here. |
| balance | the day before's wellness wheel: how evenly its eight elements shared the day |
| effectiveness | the day before. On a family day, intentions met. On a work day, half work-work against the work target and half intentions. |

The states follow Oura's: **85 and up optimal · 70 to 84 good · under 70 pay attention.**

## The card

`base_flow.js` draws the card and `base_flow.css` styles it on the now palette (`../now-palette.css`):

- **Contributor colours:** each contributor wears one of the palette's three. Teal is body (rest), ochre is balance (home), and brick is effectiveness (work).
- **The ring** is the three of them together. Each arc is that contributor's share of the number.
- **The week** is a smooth line through the mornings with a soft fill under it, and this morning is marked.

Night follows `data-theme="night"`.

```html
<link rel="stylesheet" href="now-palette.css">
<link rel="stylesheet" href="base-flow/base_flow.css">
<div id="bf"></div>
<script src="base-flow/base_flow.js"></script>
<script>
  BedoBaseFlow.render(document.getElementById("bf"), {
    parts: [{name: "body", note: "readiness this morning", value: 79}, ...],
    week:  [{label: "Mon", value: 90}, ...],   // optional
    today: 5                                    // optional
  });
</script>
```

`demo.html` shows it with example values.

Still to come: the look behind and the day ahead using the card, and nutrition joining body.
