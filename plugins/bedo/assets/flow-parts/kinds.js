/* the kinds of time and their colours: one family of hues, her own (6 Nov 2026), plus Google's
   eleven for an event that has not happened yet. gcol() is an event's calendar colour, pcol() the
   be•do colour a lived row wears, gink() the text colour that reads on it. Expects `const D` for
   D.calcolors. Lifted out of flow_engine.html, 9 Nov 2026. */
/* her own colours, picked on the page (6 Nov 2026, her words: I want to pick the colors … more vibrant, more earthy,
   a little bit of brown is good): four swatches a chunk, the first is the starting one */
/* her colours, in her words (6 Nov 2026): work in her university purple; care pink; food green; movement yellow; connection,
   play, reflection and adventures by their energy, a calm teal-blue like sitting by a still lake, or fiery when energetic;
   be•do and admin a quiet background; sleep a short night band */
/* one family (6 Nov 2026, her words: make all of these colors look like they go together): every hue at one OKLCH lightness
   and chroma (L .76, C .12), sleep a night indigo, travel an asphalt grey, admin a quiet background; yellow sits lighter so it reads yellow */
const PICKS={work:["#A272D4"],care:["#D06091"],food:["#3DA454"],move:["#DCBC33"],play:["#009ECD"],playhot:["#D46A34"],admin:["#D9CFC3"],sleep:["#403F7B"]};
/* play is what has no resistance, split by its energy: relaxation and recreation; travelling, driving or riding, is
   adventure (7 Nov 2026, her words: there's play that is relaxation and play that is recreation — their energy is the
   thing that makes them different; what characterizes play is no resistance; travelling, whether driving or riding in
   the car, is typically an adventure — that's how I like to look at it; later that day: recreation and adventure go into
   one category and keep the orange; drop that colour) */
const PICK_NAMES={playhot:'recreation and adventure · play with energy, travelling',sleep:'sleep',food:'food · eating and prep',move:'movement',care:'care · family, pets, home, you',work:'work · your profession',play:'relaxation · calm play',admin:'be•do and life admin'};
const PICK_DEFAULT=Object.fromEntries(Object.keys(PICKS).map(k=>[k,[PICKS[k][0],PICKS[k][0],PICK_NAMES[k]]]));


/* dark text on a light colour (a yellow calendar), white on the rest */
const gink=c=>{ const n=parseInt(String(c).replace('#',''),16), r=n>>16&255, g=n>>8&255, b=n&255; return (0.299*r+0.587*g+0.114*b)>165?'#2b2118':'#fff'; };
/* an event looks as it does in Google Calendar (2 Nov 2026, her words: make the colors match what is already on
   the calendar, with the box and the emoji; location, whatever we have; a link to the Google Calendar event):
   the event's own colour (Google's eleven), else its calendar's (`calendar_colors` in her settings) */
const GC={1:'#7986CB',2:'#33B679',3:'#8E24AA',4:'#E67C73',5:'#F6BF26',6:'#F4511E',7:'#039BE5',8:'#616161',9:'#3F51B5',10:'#0B8043',11:'#D50000'};
/* her own work block — work colour, nobody else on it, not a series — is a light periwinkle, never the meeting purple
   (4 Nov 2026, her words: I don't want to see the dark purple filling, because it made me think I was missing a meeting) */
const BLOCK='#AFB6E8';
/* one shade for every calendar event, and its own for one put on the calendar the same day (6 Nov 2026);
   Google's colours stay on her calendar */
/* option 1 (6 Nov 2026, her words: it's imperative that the things on my timeline match the color of the event on the
   calendar): each event wears its own Google colour, else its calendar's; last-minute is said in words, not a colour */
const gcol=x=>GC[x.color]||((D.calcolors||{})[x.who])||'#039BE5';
/* once an event has happened it wears its be•do element, pastel, and still links to the calendar event (6 Nov 2026, her
   words: when something is coming up it matches Google Calendar; after it's happened it gets the be•do color) */
const CHUNKOF={sleep:'sleep',eat:'food',cook:'food',move:'move',family:'care',pet:'care',home:'care',personal:'care',work:'work',stretch:'work',recreation:'play',moment:'play',travel:'playhot',drive:'playhot'};
const pcol=x=>{ if(!(x.cat&&x.cat!=='event')) return gcol(x); let k=CHUNKOF[x.cat==='stretch'&&x.sk?x.sk:x.cat]||'admin'; if(k==='play'&&(x.hr!=null?x.hot:(x.hot||x.el==='fire'))) k='playhot'; return (PICK_DEFAULT[k]||PICK_DEFAULT.admin)[0]; };
