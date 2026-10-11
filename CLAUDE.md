# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

An eyes-free TOEIC listening app for a Korean learner aiming at 800. The user listens while driving (~1 hour) or exercising and **cannot look at the screen**, so everything must be spoken: question numbers, every option, answers, translations. Each day is about 60 minutes of audio. Talk to the user in Korean.

## Commands

No system Python or Node is installed. Use the portable Python in `tools/python` (edge-tts is already installed there with pip):

```powershell
tools\python\python.exe build_audio.py 1        # builds Day 1 from content/day001.json
tools\python\python.exe -m pip install <pkg>    # add a package to the portable Python
```

Icons come from `make_icons.py` (Pillow), and the QR code from `make_qr.py` (qrcode). There are no tests and no lint setup. The build prints how many minutes each track runs. Use that to check a day comes to roughly 60 minutes.

## Pipeline

1. **`content/dayNNN.json`** holds the day's script, written by hand: `part2`, `part3`, `part4`, `vocab` and `news`. Every English line has a matching `ko` translation.
   - Part 3/4 options are plain strings. Only the correct one needs a Korean version (`answer_ko`).
   - Part 2 options each have `en`/`ko`, because all three are re-read with translation.
   - `accent` (US/GB/AU/CA) and `spk` (M/W, plus M2/W2 for a second man or woman in three-person conversations) choose the voice.
2. **`build_audio.py`** turns the JSON into a list of segments per track: (voice, text) pairs and pauses. The spoken order the user asked for is defined in `build_tracks()`:
   - passage + questions → thinking pause → answers → passage re-read one turn or paragraph at a time, each followed by its Korean translation
   - vocab: word → meaning → spelling → word → meaning
   - news: full read → paragraph + Korean
3. Each unique (voice, text) is synthesized once with edge-tts and cached in `cache/` under a sha1 name. A rebuild only synthesizes changed lines.
4. Tracks are joined by concatenating raw MP3 bytes. No ffmpeg is needed. This works because edge-tts always outputs MPEG-2 Layer III at 24 kHz, 48 kbps, mono CBR. Pauses are hand-built silent frames in that same format (`SILENT_FRAME`, 24 ms each). Durations are computed as bytes / 6000. If the edge-tts output format changes, this all breaks.
5. Per-track files go to `docs/audio/dayNNN/dayNNN_01..05.mp3`, and the build adds or updates that day in `docs/days.json`. The single full-day file goes to the git-ignored `audio/` folder for local use only. Each file gets a hand-written ID3v2.3 tag.

## App and publishing

`docs/` is an installable PWA, served by GitHub Pages from `/docs` on `main`. The repo is `toeic800` on the user's account. The user has an Android phone.

- `index.html` is the one-screen player. It lists days from `days.json`, so adding a day needs no HTML edit. When a newer day appears, it jumps to that day once. Otherwise it resumes the saved position from localStorage. Media Session handlers let car and Bluetooth buttons work.
- `sw.js` serves the app network-first. MP3s are cached only when the user taps 저장 for a day. Cached MP3s are answered with hand-built 206 responses, because `<audio>` sends Range requests. Bump `SHELL` when shell files change.
- `qr.png` is the install QR code. `make_qr.py <url>` creates it. On desktop the page shows it so the phone can scan it.

To publish a new day: build it, then run `.\publish.ps1 "Add Day N"`. The script commits, pushes and, on its first run, creates the repo, enables Pages and makes the QR code. It needs `gh auth login` done once. Git and gh were installed with winget, so a shell that was already open may need its PATH refreshed.

A GitHub Pages site is limited to about 1 GB, and each day adds about 24 MB. After roughly 40 days, old days will have to be removed.

An earlier player still exists as a claude.ai Artifact: https://claude.ai/artifact/KSnCAxCvWdhKkxmKGk6cXK (source `player/`, git-ignored). It only contains Day 1.

## Content rules

- Real ETS/TOEIC questions are copyrighted. Write original TOEIC-style items instead.
- News: Korea-related stories from CNN and similar outlets, **rewritten** in your own words from real reporting. Never copy article text. Keep claims to facts you can source, and don't invent quotes or analysts.
- Vocab: about 25 words at Korean high-school year-1 level, taken from that day's passages.
- Target sizes that give about 60 minutes:
  - Part 2: 15 items
  - Part 3: 5 sets
  - Part 4: 4 talks
  - Vocab: 25 words
  - News: 2 articles of about 4 paragraphs each
