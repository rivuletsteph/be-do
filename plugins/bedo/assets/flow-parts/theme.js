/* Shared by every be•do page: the my day page and the my week page. Lifted out of
   flow_engine.html, 9 Nov 2026 — one copy, so the pages cannot drift apart. */
/* light or dark: one button, like the Morning Gate and the morning news (7 Nov 2026, her words: it defaults to
   the setting I already have, and then it's just one button). The page opens as the device is set; the button flips it
   for this look, and the next open follows the device again. ?theme=light|dark overrides. */
(function(){var h=document.documentElement,q=location.search.match(/[?&]theme=(light|dark|day|night)/),o=q?(/dark|night/.test(q[1])?"night":"day"):null,m;
function dev(){return window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"night":"day"}
function set(w){if(h.getAttribute("data-bedo")!==w){h.setAttribute("data-bedo",w);document.dispatchEvent(new Event("bedo-theme"))}}
window.bedoThemeNow=function(){return o||dev()};
window.bedoThemeFlip=function(){o=window.bedoThemeNow()==="night"?"day":"night";set(o)};
try{localStorage.removeItem("bedo-theme")}catch(e){}
set(window.bedoThemeNow());
if(window.matchMedia){m=matchMedia("(prefers-color-scheme: dark)");(m.addEventListener?m.addEventListener("change",function(){if(!o)set(dev())}):m.addListener(function(){if(!o)set(dev())}))}})()
