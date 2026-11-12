/* the eight wellness elements and their glyphs — her own simple monotone line icons, in their
   wheel colours (6 Nov 2026, her words: the symbol is really what I am going off of). WDOM holds
   each element's fill, its stroke, where it sits on the wheel and what it means; wicon(k, size)
   draws one. Lifted out of flow_engine.html, 9 Nov 2026. */
const WDOM={heart:{c:"#3E7FD0",d:"#245693",a:247.5,f:"connection · love · care"},water:{c:"#9BC4F5",d:"#4C95ED",a:67.5,f:"connecting · advocacy · community"},
 mind:{c:"#BE4A88",d:"#822F5C",a:292.5,f:"thinking · planning · learning"},air:{c:"#F49CC8",d:"#EB4E9D",a:112.5,f:"systems · technical · digital"},
 body:{c:"#4E9E62",d:"#31643E",a:202.5,f:"health · movement · rest"},earth:{c:"#97D8A3",d:"#58C06B",a:22.5,f:"tending · maintaining · admin"},
 spirit:{c:"#EFA038",d:"#C17410",a:337.5,f:"meaning · values · joy"},fire:{c:"#F7CE72",d:"#F2B120",a:157.5,f:"creating · transforming · play"}};
const WPAIRS=[["body","earth"],["heart","water"],["mind","air"],["spirit","fire"]];
/* the wellness symbols, as the stream spells them (6 Nov 2026, her words: the symbol is really what I'm going off of) */
/* the wellness glyphs are the look behind's own simple line icons (6 Nov 2026, her words: very simple monotone glyphs
   that I've had in different versions of the wellness wheel), copied from bedo-look-behind's engine */
const WICON = {
  heart: `<path d="M10 17.2 3.4 10.8A3.9 3.9 0 0 1 10 5.6a3.9 3.9 0 0 1 6.6 5.2Z"/>`,
  water: `<path d="M2 8.5c2-2.2 4-2.2 6 0s4 2.2 6 0 3-1.4 4-1M2 13.5c2-2.2 4-2.2 6 0s4 2.2 6 0 3-1.4 4-1" fill="none" stroke-width="2.2" stroke-linecap="round"/>`,
  mind:  `<path d="M10 3.2c-1.6-1-3.8-.3-4.3 1.5-2 .1-3 2.2-2.1 3.8-1.2 1.3-.8 3.6 1 4.2.1 2 2.2 3.1 3.9 2.2.6.9 1.5 1.3 1.5 1.3s.9-.4 1.5-1.3c1.7.9 3.8-.2 3.9-2.2 1.8-.6 2.2-2.9 1-4.2.9-1.6-.1-3.7-2.1-3.8C13.8 2.9 11.6 2.2 10 3.2Z"/><path d="M10 3.4v12.8" fill="none" stroke-width="1.2"/>`,
  air:   `<path d="M2 7.5h9.5a2.5 2.5 0 1 0-2.4-3.2M2 11h13.5a2.5 2.5 0 1 1-2.4 3.2M2 14.5h6" fill="none" stroke-width="2.2" stroke-linecap="round"/>`,
  body:  `<circle cx="10" cy="3.8" r="2.2"/><path d="M4 7.8 10 9l6-1.2M10 9v3.6M10 12.6 6.2 17.4M10 12.6l3.8 4.8" fill="none" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`,
  earth: `<circle cx="10" cy="10" r="7.4"/><path d="M2.8 10h14.4M10 2.6c-2.6 2.2-2.6 12.6 0 14.8M10 2.6c2.6 2.2 2.6 12.6 0 14.8" fill="none" stroke-width="1.1"/>`,
  spirit:`<path d="M10 1.8 11.9 8.1 18.2 10 11.9 11.9 10 18.2 8.1 11.9 1.8 10 8.1 8.1Z"/>`,
  fire:  `<path d="M10 18.2c-3.6 0-6-2.4-6-5.6 0-2.6 1.7-4.2 3-5.8.2 1.4.9 2.4 1.8 2.8C8.4 6.4 9.9 3.8 12.2 1.8c-.2 2.6.8 4.2 2 5.8 1 1.4 1.8 2.9 1.8 5 0 3.2-2.4 5.6-6 5.6Z"/>`
};
const wicon=(k,s)=>`<svg viewBox="0 0 20 20" width="${s}" height="${s}" aria-hidden="true" style="overflow:visible;vertical-align:-2px"><g fill="${WDOM[k].c}" stroke="${WDOM[k].d}" stroke-width="1" stroke-linejoin="round">${WICON[k]}</g></svg>`;
