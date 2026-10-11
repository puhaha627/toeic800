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

There are no tests and no lint setup. The build prints how many minutes each track runs. Use that to check a day comes to roughly 60 minutes.

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
5. Output goes to `audio/dayNNN/dayNNN_01..05.mp3`, plus `dayNNN_00_full.mp3`. Each file gets a hand-written ID3v2.3 tag.

## Player and publishing

`player/index.html` is a one-screen player published as a claude.ai Artifact: https://claude.ai/artifact/KSnCAxCvWdhKkxmKGk6cXK

It has:
- a large play button
- automatic advance to the next track
- Media Session handlers, so car and Bluetooth buttons work
- the listening position saved in localStorage

To add a day:
1. Add an entry to the `DAYS` array, using the per-track minutes the build printed.
2. Republish `player/index.html` to the same URL, with the new MP3s passed in `files`. Map each file to the same path: `audio/dayNNN/dayNNN_0X.mp3`.

Upload only the per-track files. The `_00_full.mp3` file (about 23 MB) is over the 15 MB limit for one artifact file.

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
