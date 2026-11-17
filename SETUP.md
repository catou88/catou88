# Setup (about 5 minutes)

1. **Create your profile repo.** On GitHub, make a new public repo named exactly `catou88`. GitHub shows its README on your profile page.
2. **Upload everything in this folder** (keep the folder structure): `README.md`, `profile.json`, `assets/`, `scripts/`, `.github/workflows/profile.yml`. You don't need to upload `SETUP.md` or `quest-map-preview.gif`.
3. **Let the workflow write.** Go to Settings → Actions → General → Workflow permissions, choose "Read and write permissions" and save.
4. **Run it once.** Go to Actions → "Refresh profile cards" → Run workflow. It fills in your level, lifetime contributions, commits and PRs, and builds the city skyline from your real last 52 weeks. After that it runs daily.
5. *(Optional)* To count **private** contributions too, create a classic personal access token with the `read:user` scope. Add it under Settings → Secrets → Actions as `PROFILE_TOKEN`.

## Editing

Everything you might want to change is in `profile.json`:

- `quests`: one island each, flown left to right. Change the order to match when you built them. Each quest has a `name`, a `tech` line and a `tag` (`CO-OP` shows in pink, `WINNER` in gold, `HACKATHON` in cyan, anything else in mint; `NOW BUILDING` also gets a blinking dot). The `icon` can be `dumbbell`, `database`, `star`, `trophy`, `magnifier`, `badge`, `butterfly`, `book` or `beacon` (unknown names fall back to `beacon`). Keep each text line to about 14 characters.
- `manual_stats`: hackathon wins and team projects. GitHub can't count these for you.
- `achievements`, `loadout`, `role`: the text on the player card.

Push a change to `profile.json` and the workflow re-renders the cards. To preview locally, run `python3 scripts/gen.py` and open the SVGs in a browser. No installs are needed.
