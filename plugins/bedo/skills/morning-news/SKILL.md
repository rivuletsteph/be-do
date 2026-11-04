---
name: "morning-news"
description: "The user's morning news roundup, published as a one-reader newspaper page: the places, topics and newsletters they follow, with photos. Use when the user asks for the morning news, the news, the paper, or what's new on any topic or place in their news settings."
---

# Morning news: the paper

A short roundup of what's new in the places, topics and newsletters the user
follows. It is delivered as a one-reader newspaper page published as an
Artifact, with a short pointer in chat. On demand for now; it may later be
scheduled or folded into the dawn flow.

**Nothing personal lives in this skill.** The masthead, topics, places,
preferred outlets and newsletter senders all come from the settings.

## 1. Get the settings

Read the `morning_news_local` row of the `settings` table in the `be•do system`
base (`core/bedo_settings.py`; base and table found by name). Its shape is
`assets/morning_news_local.example.json`:

- `masthead`: the paper's name.
- `topics`: in order, each with what to look for. The first topics lead.
- `places`: each with its local outlets, and any page to fetch directly.
- `preferred_outlets`: e.g. a paper the user subscribes to, for its region's stories.
- `newsletter_senders`: the addresses for the Gmail search.
- `notes`: what they've said they want more or less of, in their words.

If the row can't be read, fall back to the memory file `/topics/news-interests.md`.
If neither exists, say so in one line and ask for the list. Never guess one.

## 2. Newsletters: inbox and queue

**Gmail.** One `search_threads` call for the senders, since the last run
(default `newer_than:1d`; Mondays `newer_than:3d`):

```
from:(<sender> OR <sender> OR …) newer_than:1d
```

Read only the threads whose subject touches the topics or places, or is a daily
briefing (a national morning newsletter, a state politics brief, a local paper).
Pull the headlines and links from inside them. **Read only: never archive,
label or mark read.** Clearing the inbox is the `clear-inbox` skill's job.

If a newsletter sender shows up that isn't in the list, mention it once and ask
whether to add it.

**be•do queue.** Read this week's stream (resolve `w## be•do` by name;
bedo-airtable skill) for `📰 news` rows that are still open, and for
`queue` = true reading rows. They go in **From your queue**, title and state,
so saved pieces don't get lost. Don't change them.

## 3. Search

- One standard search per topic and place; fetch any listed page directly.
  Skip a search when the newsletters already covered that topic well today.
  When a standard search comes back thin or stale on a big topic, run one
  extended search.
- For the bigger stories, also search YouTube for a recent video (news segment,
  interview, briefing) and include it when one is relevant and from the last
  few days.
- Look back about 24 hours. On Mondays, cover the weekend (back to Friday morning).
- If something has nothing new, say so in one line. Don't pad it with older stories.
- Skip opinion pieces, ads and obituaries unless asked, or unless it's from a
  newsletter the user subscribes to.

## 4. Photos

Real photos make the paper. Aim for one per section that has a fitting one,
and always one for the lead.

- **Where from:** the story's own `og:image` (curl the article with a browser
  user agent, grep the `og:image` meta tag). When an outlet gives nothing, try
  another outlet covering the same story. YouTube thumbnails come from
  `https://img.youtube.com/vi/<id>/maxresdefault.jpg`.
- **Look before you use one.** Make a contact sheet and view it. **Skip a
  thumbnail with clickbait overlays** ("LEAVE NOW!", "BREAKING", big text) or
  one that looks AI-made, and use a real news photo instead. An image that
  clearly shows a different event (an older file photo) runs only as a file
  image, captioned as one.
- **Every photo gets a caption and a credit:** what it shows and when, if the
  source says, then the outlet or photographer. Never write a caption the
  source doesn't support.
- **Ship them with the page.** The artifact's CSP blocks outside images, so
  download each into its own scratchpad folder, resize to an 800–1200px wide
  JPEG (`convert -resize 1200x -quality 78`), and publish them through the
  Artifact tool's `files` as `img/<name>.jpg`.
- A section with no usable photo runs without one. Don't fill the space with a
  stock or decorative image.

## 5. Report: the paper

Build the page from `reference/paper-template.html`. Keep its palette, type and
layout, and fill in the slots. Read the `artifact-design` guidance (or run the
Artifact quickstart) before the first publish of a session.

- **Masthead:** the settings' `masthead`. The dateline gives the weekday and
  date, any flag for the day (an election, a holiday, a storm), and the read time.
- **Lead story:** the day's biggest story among the topics and places, with the
  big photo, a deck line, a short body with links, and a ▶ Watch link when
  there's a good video.
- **Side box:** the day's second thread when there is one (an election, a vote,
  a hearing). Otherwise use the next story.
- **Sections:** one cell per topic or place, with one to three stories each. A
  place with nothing new gets one quiet line.
- **In your inbox:** one line per newsletter, its sender, then the one to three
  headlines that matter.
- **From your queue:** the be•do rows, title and state, unchanged.
- **Colophon:** one line saying where the paper was gathered from.

**Always the headline and the link:**
- The story's headline as the link text, then one plain line on what happened.
- State it plainly. No hype, no "reveal" framing, no conclusions nobody asked for.
- Political and war stories, and political newsletters: what was said,
  evenhanded, no verdicts.

Keep it short enough to read in about three minutes. **Publish a new artifact
each day** (a new file path, `morning-paper-YYMMDD.html`, titled with the
masthead and the date, e.g. "<masthead> · Tue 3 Nov"), so earlier editions stay
readable.

**In chat:** the link, then the top two or three headlines in one line each,
then anything you couldn't do (no settings row, a section with no results, a
link that only goes to the inbox). Don't repeat the whole paper in chat. When
this runs as a spin-off of the my day chat, the pointer sent back to the parent
is the link plus the top headlines.

## 6. Learn and log

- When the user reacts ("more like this", "skip that", "add X", "drop that
  newsletter"), update the `morning_news_local` row's `notes` (or the list it
  names) with what they said, in their words.
- If they ask to keep a story, log it in be•do as a `📰 news` practice row
  (bedo-airtable skill), the way earlier news rows were logged.
