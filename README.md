<div align="center">

<img src="assets/hud.svg" width="100%" alt="CATOU88 player card: level, lifetime contributions, commits, collab repos, 1 hackathon win, 2 hackathon entries, 4 team projects">

<img src="assets/quest-map.svg" width="100%" alt="Quest log: a cat flies a blimp over eight floating islands, one for each project, above a city built from my contribution graph">

</div>

### Quest log

| | Project | What it is |
|---|---|---|
| 🏆 | [**Orkio**](https://github.com/catou88/OrkioDemo): Cal Hacks winner | Agent Cowork: hooks and an MCP server that let each teammate's Claude Code agent own a module of a shared repo while an orchestrator keeps their changes compatible |
| 🔍 | [**MantisGrid**](https://github.com/catou88/hackathon-2026-official): hackathon | A Dockerized root-cause-analysis agent that answers incident queries with a best guess plus a written evidence file for each one |
| 🪪 | [**Lanyard**](https://github.com/catou88/SlackRetrieval) | Saves a Slack workspace offline, builds a contact book, and answers questions over it with local-embedding search and Claude |
| 🦋 | [**ButterflAI**](https://github.com/catou88/butterflai2) | Models sunspot emergence as a spatiotemporal point process with classical and AI models (COFFIES Science Center research program) |
| 📚 | [**LegalLibrary**](https://github.com/catou88/LegalLibrary): now building | Legal tech project, just getting started |
| 🗄️ | [**AlgoDB Lab**](https://github.com/catou88/GoDatabase) | A durable B+Tree store in Go, plus a Next.js visualizer that traces operations through the WAL, the buffer pool and the disk |
| 🌌 | [**Asterism**](https://github.com/vibhutirp/asterism) | Clusters store-purchase behavior into a 3D galaxy map, built with Streamlit and Snowflake |
| 🏋️ | [**Workout App**](https://github.com/thomassems/MyWorkoutApp) | A team-built Java app for searching, filtering and saving workouts |

<sub>The cards refresh daily from my GitHub activity. The skyline at the bottom of the quest log shows my last 52 weeks of contributions, and taller buildings mean busier weeks.</sub>

<details>
<summary><b>How this profile works</b></summary>

<br>

Both cards above are plain SVG files drawn entirely from rectangles by a small Python generator. They use no web fonts, no JavaScript and no third-party stats service, so GitHub renders them as is. The animation is CSS keyframes inside the SVG, and it switches off for viewers who set `prefers-reduced-motion`.

#### Repository layout

| Path | Purpose |
|---|---|
| `profile.json` | Everything you edit by hand: name, role, loadout, achievements, hackathon counts and the list of quests (islands). |
| `scripts/pixel.py` | A tiny pixel-art toolkit: a 5×7 bitmap font, sprite drawing, and a `Canvas` that merges pixels into one `<path>` per colour to keep the files small. |
| `scripts/gen.py` | Renders `assets/hud.svg` (player card) and `assets/quest-map.svg` (blimp tour and contribution city) from `profile.json` and `data/stats.json`. |
| `scripts/fetch_stats.py` | Calls the GitHub GraphQL API and writes `data/stats.json`: lifetime contributions, commits, PRs, repos contributed to and the last 52 weeks of activity. |
| `.github/workflows/profile.yml` | Runs fetch, then render, then commit. It runs daily at 09:17 UTC, on manual dispatch, and on pushes that touch `profile.json` or `scripts/`. |
| `assets/` | The generated SVGs. Don't edit these by hand, because the next run overwrites them. |
| `data/stats.json` | Created by the workflow on its first run. It is committed so that local renders can reuse it. |
| `SETUP.md` | A short checklist for first-time setup. |

#### Data flow

```
GitHub GraphQL API ──fetch_stats.py──▶ data/stats.json ─┐
                                                        ├─gen.py──▶ assets/hud.svg
profile.json ───────────────────────────────────────────┘          assets/quest-map.svg
```

#### How the numbers are calculated

- **Level** = `floor(sqrt(lifetime contributions / 2)) + 1`. The XP bar shows the progress toward the next level.
- **Lifetime contributions / commits** are summed over every year listed in `contributionYears`. Commits also include `restrictedContributionsCount` (private contributions). That count is only non-zero when the workflow uses a personal token, `PROFILE_TOKEN`.
- **Collab repos** counts repositories you don't own that you contributed commits, PRs or repos to.
- **Hackathon wins, hackathon entries and team projects** come from `manual_stats` in `profile.json`, because GitHub can't count these.
- **City skyline**: one building per week. Height scales with `(week / busiest week)^0.8`, and the busiest week gets an antenna. Until `data/stats.json` exists, the skyline is procedural and the live tiles show `--`.

#### Editing quests

Each entry in `quests` becomes one island. Islands are visited left to right, and anything past 5 wraps onto a second row.

```json
{ "name": "ALGODB LAB", "tech": "GO + NEXT.JS", "tag": "B+TREE ENGINE",
  "icon": "database", "repo": "https://github.com/catou88/GoDatabase" }
```

- **Icons:** `dumbbell`, `database`, `star`, `trophy`, `magnifier`, `badge`, `butterfly`, `book`, `beacon`. Any other name falls back to `beacon`.
- **Tag colours:** `WINNER` is gold, `CO-OP` is pink, `HACKATHON` is cyan, and anything else is mint. `NOW BUILDING` also gets a blinking cursor.
- **Text:** keep each line to about 14 characters. The font covers A–Z, 0–9 and `. : - / + ! ? # & > = ' %`, and any other character renders as `?`.

#### Run it locally

You need Python 3 and nothing else.

```sh
python3 scripts/gen.py                     # renders with data/stats.json if it exists
GH_TOKEN=$(gh auth token) python3 scripts/fetch_stats.py   # optional: pull live stats first
open assets/hud.svg assets/quest-map.svg   # preview in a browser
```

#### First-time GitHub setup

1. This repo must be public and named exactly `catou88`.
2. Go to **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions**.
3. Go to **Actions → Refresh profile cards → Run workflow** once to fill in the live stats.
4. *(Optional)* Add a classic PAT with the `read:user` scope as the repo secret `PROFILE_TOKEN`, so the counts include private contributions.

</details>
