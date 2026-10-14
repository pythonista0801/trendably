# Trendably — handover

Trendably is an S&P 500 learning and analysis app: see the market, compare stocks and sectors, test one strategy on one stock, and learn how it all works. This folder holds the finished **design and layout** for every page. All figures are **sample data**; all lesson and tale content beyond one lesson is a **sketch**. The next job is wiring: a live data feed, AI-generated lessons, and shared progress.

Read the locked design rules before changing any page.

**`DATA-SPEC.md` is the companion to this file:** every figure on every page, its data stream, its exact calculation, its refresh rate, where the placeholder sits in the code and what replaces it. Read it before wiring any data. The backtest engine already exists in `backend/` — wire it, don't rebuild it (DATA-SPEC Part I).

---

## 1. Run it

```
cd trendably
python -m http.server 8000
# open http://localhost:8000/index.html
```

Use a local server, not double-clicking files: the lesson template loads `lessons/*.json` with `fetch`, which browsers block on `file://`. (Every page still opens from `file://`; the lesson just falls back to its built-in copy.)

## 2. Folder

```
index.html              Landing
market-weather.html     Market Weather — "Is today a good day to invest?"
the-grid.html           The Grid — build a stock-versus-strategy grid
sector-technology.html  Sector page (Information Technology; template for all 11)
industry.html           Industry page template (?ind=<slug>)
stock-detail.html       Stock Detail (?sym=<ticker>)
strategy-lab.html       Strategy Lab (?sym=<ticker>&strat=<id>)
study-room.html         Study Room — landing, tiers, chapters, Tales of Markets
study-lesson.html       Lesson TEMPLATE — renders any lesson from JSON
lessons/<tier>/<chapter>/<lesson>.json   one file per lesson
data/market-sample.json sample market snapshot used by lessons
HANDOVER.md             this file
DATA-SPEC.md            data streams, calculations, placeholders, page by page
backend/                the existing FinStrategyGrid backtest engine (real prices) — see DATA-SPEC Part I
universe.json           which S&P 500 stocks the engine covers
requirements.txt        Python packages for the engine
cache/                  created by the engine; downloaded prices (not committed)
```

Pages link to each other by these exact file names. Keep them.

## 3. Locked design rules (do not change without Natalie)

- **One design, two modes.** Each page is one file with a light and a dark CSS variable set on `:root` and `:root[data-mode="dark"]`, and a sun/moon toggle. The attribute is `data-mode` (not `data-theme`); the choice persists in `localStorage['tb-mode']`.
- **Palette: navy, electric blue, cyan.** No yellow or gold anywhere, and never as a good/bad scale. The only warm colours allowed are the four Market Weather emotion bars (`--emo-fear`, `--emo-unc`, `--emo-opt`, `--emo-conf`).
- **Tokens** (light / dark): `--bg #FFFFFF/#05080E`, `--panel #F4F9FE/#0D1420`, `--panel2 #EAF3FC/#121A27`, `--border #C9DCF2/#2A3850`, `--text1 #0B1C33/#F3F6FB`, `--text2 #33547A/#B7C0D1`, `--text3 #5A7699/#8593A8`, `--blue #1C6FE0/#2F8CFF`, `--cyan #0EA5C4/#21D4F0`, `--green #0E9F6E/#2EE6A6`, `--red #D23A58/#FF5577`. Copy the full sets from any page's `<style>`.
- **Type.** Sora for headings, Inter Tight for body. Every page's main heading is **Sora 22px / 600**; sub-headings 17px / 600. Only the Landing hero is larger (≈33px / 700).
- **Section header gradient** (settled): light `linear-gradient(180deg, rgba(28,111,224,.92) 0%, rgba(14,165,196,.5) 65%, rgba(255,255,255,0) 100%)`; dark `linear-gradient(180deg, rgba(47,140,255,.30) 0%, rgba(33,212,240,.10) 70%, rgba(13,20,32,0) 100%)`.
- **Width.** Content column 780px max; must not scroll sideways at 390px (phone).
- **Every ticker is clickable** to `stock-detail.html?sym=<TICKER>`.
- **Structure is nested:** market → sector → industry → stock. One data-driven template per level, never one hand-made page per sector or industry.
- **Study Room navigation:** Study Room → tier → chapter → lesson → concepts. Rich image tiles only at the front door (the four tier tiles); quiet numbered lists inside. Concepts flow down one lesson page — no page per concept.
- **The tutor explains how markets work. It never recommends buying, selling or holding, and never predicts prices.**

## 4. Pages

All pages share the nav bar, the drawer menu, the mode toggle and the tokens above. **Each file contains both light and dark mode**; there are no separate dark files. Every page opens in light by default (`<html data-mode="light">`) and switches with the sun/moon button; the choice is remembered in `localStorage['tb-mode']` across all pages. (The published preview links come in light and dark pairs only because each link opens the same file with a different starting mode.)

**index.html — Landing.** Hero, the four journey cards, links into every page. Static. No data.

**market-weather.html — Market Weather.** Index strip, mood gauge, four emotion bars (fear, uncertainty, optimism, confidence), sector moves. Sample data in `var SEC` (sectors) and `var EMO` (emotions). Needs: index and sector moves, plus a defined signal for each emotion. Open: link the mood gauge to the driver cards; show a "refreshed every 15 min" time stamp.

**the-grid.html — The Grid.** Pick stocks and strategies; shows each stock's historical return per strategy. `MAX_STOCKS` caps the selection. Sample returns are embedded. Needs: per-stock strategy backtest results. Open: keep or remove the "Today's sector moves" block.

**sector-technology.html — Sector page.** One sector, its industries (`var IND`) and today's moves (`var TODAY`). Make it a template driven by `?sector=<slug>` and load the other ten sectors with their real GICS industries.

**industry.html — Industry page.** Already a template: `?ind=<slug>` (default `semiconductors`). Data in `IND`, `TODAY`, `SPX_W` (S&P weights). Needs the real GICS industries and constituents.

**stock-detail.html — Stock Detail.** Header, composite score, measures, glossary pop-up (`.gl-sheet`, seven terms). Content in `ITEMS`, `SYM`, `SUBTITLE`. To do: read `?sym=` and load from shared stock data (today it shows sample NVDA). Composite score = Momentum 0.30, Risk 0.20, Valuation 0.20, Fundamentals 0.30 — **proposal, not confirmed**. Optional extras: "where it sits", compact strategy results, price chart, news slot.

**strategy-lab.html — Strategy Lab.** Tests one strategy on one stock. Deep link `?sym=AAPL&strat=bb`. Contains real ticker data for the finished bar; tuning constants `OUTPERF_*`, `START`.

**study-room.html — Study Room.** Views (one file, switched by `go(id)`):
- `vEntrance` — hero, Continue-learning card, four tier tiles (Foundations, Practitioner, Mastery, Tales of Markets).
- `vTierList` — a tier's chapters. `vChapter` — a chapter's lessons. Both are **rendered from the curriculum JSON** in `<script id="curriculum">`.
- `vTales` — five shelves of 16 tales (titles only; content to write).
- Deep links: `#foundations`, `#practitioner`, `#mastery`, `#<chapter-id>`, `#tales`.
- Row states: *Being written* (dashed, no content), *Not started*, *In progress* (blue number, blue bar), *Finished* (cyan check, cyan bar).
- Hero stats, tile counts and the Continue card are all computed from the curriculum plus `tb-study` progress.
- The Tales of Markets banner and shelf header stay night-coloured in both modes on purpose ("after hours").

**study-lesson.html — Lesson template.** Renders one lesson: sticky breadcrumb and five-bar progress, concept cards (read → app snapshot → common mistake → multiple-choice check → explore with the tutor), recap, next lesson. Tutor is a bottom sheet. See section 5.

## 5. Data contracts

### 5.1 Market snapshot — `data/market-sample.json`
The lesson template reads it from `<script id="market-data">`. Replace with the live feed in the **same shape**:
```json
{ "asOf": "2026-10-14T15:45:00-04:00",
  "index":  { "name": "S&P 500", "level": 6612.40, "points": -39.90, "move": -0.6 },
  "strip":  [["S&P 500", -0.6, "%"], ["NASDAQ", -0.9, "%"], ["Dow Jones", -0.2, "%"], ["VIX", 16.1, ""]],
  "sectors":[{ "name": "Information Technology", "weight": 38, "move": -1.4 }, ...] }
```
`move` and `weight` are percentages. Index and sectors must come from the **same feed and moment** so they agree. Planned source: Yahoo Finance.

### 5.2 Lesson — `lessons/<tier>/<chapter>/<lesson>.json`
Loaded by `study-lesson.html?lesson=<id>`; the id is the path without `.json`.
```json
{ "id": "foundations/market-as-a-whole/what-an-index-is",
  "tier":    { "id": "foundations", "title": "Foundations" },
  "chapter": { "id": "market-as-a-whole", "title": "The market as a whole" },
  "number": 1, "lessonsInChapter": 4, "minutes": 12,
  "title": "What an index is",
  "intro": "One or two sentences.",
  "concepts": [{
     "title": "What an index measures",
     "read": ["Paragraph.", "Paragraph."],
     "aside": "Optional analogy.",
     "snapshot": { "type": "strip", "where": "Market Weather · top strip", "caption": "One sentence." },
     "mistake": "Optional common mistake.",
     "question": { "prompt": "…", "options": [
        { "text": "…", "feedback": "Why this is wrong." },
        { "text": "…", "feedback": "Why this is right.", "correct": true } ] },
     "explore": ["Tutor starter question", "Another"] }],
  "recap": ["One line per concept."],
  "next": { "id": "foundations/market-as-a-whole/sectors-and-industries", "title": "Sectors and industries" },
  "tutorContext": "Where nearby topics are taught, for the tutor." }
```
**Snapshot types** (drawn from the market snapshot): `strip`, `grid`, `weights`, `quote`, `moves`. An unknown type shows a placeholder box — add new types in `snapshot()` in the template.

**Live figures in text: use tokens, never type today's numbers.** Any string can contain:
`{{index.move}}` `{{index.moveSigned}}` `{{index.level}}` `{{index.points}}` ·
`{{best.name}}` `{{best.moveSigned}}` `{{worst.name}}` `{{worst.moveSigned}}` `{{largest.name}}` `{{largest.moveSigned}}` `{{largest.weight}}` ·
`{{top2.weight}}` `{{count.up}}` `{{count.down}}` ·
`{{sector:<Name>.weight}}` `{{sector:<Name>.move}}` `{{sector:<Name>.moveSigned}}`.
An unknown token renders as "—". Historical examples (e.g. "the early 1990s, when the index sat near 400") stay as plain text.

### 5.3 Curriculum — `<script id="curriculum">` in `study-room.html`
Tiers → chapters → lessons. A lesson with `"live": true` has a JSON file and opens; others show *Being written*. When a new lesson file is added, add `"live": true`, `"concepts"` and `"minutes"` to its entry. Consider moving this block to `data/curriculum.json`.

### 5.4 Progress — `localStorage['tb-study']`
```json
{ "<lesson id>": { "done": [0, 1], "at": 2, "updated": 1734567890000, "title": "…", "concepts": ["…"] } }
```
`done` = concept indexes answered correctly; `at` = concept the learner last reached. The lesson writes it; the Study Room reads it. Move to the user account when sign-in exists.

## 6. Generating lessons with an AI model

The model writes **only lesson JSON** (5.2), never HTML. Rules to give it:
- 4–6 concepts per lesson; each a short read (2 paragraphs, plain words), one snapshot, an optional common mistake, one question.
- Questions are **multiple choice, phrased differently from the lesson text**, 3–4 options, exactly one `correct`. Every option has feedback that explains why.
- Any figure about today's market uses a token from 5.2.
- Each snapshot is a real Trendably screen; `where` names it ("Market Weather · sector weights").
- No buy/sell/hold advice, no price predictions.
- Validate against the schema before saving; reject a file with no correct option or an unknown snapshot type.

Chapter titles for all three tiers are already in the curriculum. Foundations chapter 4 has its four lesson titles; the rest need lesson lists.

## 7. Open decisions (Natalie)

- Points: earned per concept or per lesson; what counts as "understood"; what free vs Core users earn.
- Composite score weights (0.30 / 0.20 / 0.20 / 0.30).
- Keep or remove the Grid's "Today's sector moves".
- Question banks per lesson (Natalie may source from ChatGPT; they still need to fit 5.2).

## 8. To do, in order

1. Shared data layer: one market snapshot and one stock dataset that every page reads (replaces all sample arrays).
2. Stock Detail reads `?sym=`; sector page becomes `?sector=` template; load all 11 sectors and their GICS industries.
3. AI lesson generation into `lessons/`; update curriculum `live` flags.
4. Glossary pop-up on every page (Market Weather incl. the four emotions, Grid, sector, industry); write remaining terms.
5. Tales of Markets content (16 tales).
6. News per biggest mover; emotion bars from their own signals; 15-minute refresh stamp.
7. Accounts: move `tb-study` progress and `tb-mode` to the user profile.
