/* times end in a lowercase a or p (her amendment of 9 Nov 2026: 9:00a, 2:45p —
   no space, no m, no AM/PM). wt("14:45") -> "2:45p". Lifted out of flow_engine.html, 9 Nov 2026,
   so every page formats a time the one way. */
const wt=h=>{const [a,b]=h.split(':').map(Number);return `${a%12||12}:${String(b).padStart(2,'0')}${a<12?'a':'p'}`;};
