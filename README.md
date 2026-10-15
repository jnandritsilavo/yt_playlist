# YT Playlist Pro

*[Version française → README.fr.md](README.fr.md)*

A desktop application and command-line tool to download YouTube playlists in HD,
built on top of [yt-dlp](https://github.com/yt-dlp/yt-dlp). Analyze a playlist,
pick the videos you want, choose a quality, and watch the progress in a clean
dark or light interface.

The project ships two front ends sharing the same engine (yt-dlp + ffmpeg + Deno):

| File | What it is |
| --- | --- |
| `yt_playlist_gui.py` | **Graphical interface (recommended).** No extra dependency: uses Tkinter, bundled with Python. |
| `yt_playlist.py` | Minimal interactive command-line version, unchanged. |

## Features

### Graphical interface

- **Analyze before downloading**: lists every video of a playlist with its duration and total length.
- **Selection**: checkboxes per video, plus *Select all / none / invert*.
- **Quality choices**: best available, 4K, 2K, 1080p, 720p, 480p, 360p, or **audio only** (MP3 192 kbps / M4A).
- **Live progress**: per-video bar, overall bar, speed, ETA and a status for each row
  (waiting, downloading, processing, done, error, cancelled).
- **Cancel at any time**, without freezing the window; one failing video never stops the rest.
- **Dark and light themes**, **French and English** interface, switchable on the fly.
- **Settings remembered** between sessions (`~/.yt_playlist_pro.json`).
- **Health badges** for ffmpeg and Deno; click one for installation help.
- **Clipboard detection**: a copied YouTube link is pre-filled when you open the app.
- Built-in log tab, *Open folder* button, optional AAC audio, cookies file or browser cookies.

### Output (both versions)

- Video and audio merged into a single MP4 through ffmpeg.
- Files numbered in playlist order, kept even if you only select some videos:
  `01 - First video.mp4`, `04 - Fourth video.mp4`, ...
- One folder per playlist, named after the playlist. A single video is saved directly in the output folder.

## Requirements

- Python 3.8 or newer, with Tkinter (included in the official Windows and macOS installers;
  on Debian/Ubuntu: `sudo apt install python3-tk`)
- yt-dlp and imageio-ffmpeg
- Deno, used to solve YouTube's JavaScript challenges

```bash
pip install -r requirements.txt
```

or, to get the latest yt-dlp build:

```bash
pip install -U --pre "yt-dlp[default]" imageio-ffmpeg
```

### Deno

Since 2026, YouTube requires a JavaScript runtime to resolve player signatures.
Without Deno, most downloads fail with `HTTP Error 403: Forbidden`.

Windows:

```powershell
winget install DenoLand.Deno
```

or

```powershell
irm https://deno.land/install.ps1 | iex
```

macOS and Linux:

```bash
curl -fsSL https://deno.land/install.sh | sh
```

As a last resort, download `deno.exe` from the
[Deno releases page](https://github.com/denoland/deno/releases) and place it in the
same folder as the scripts; they add their own directory to `PATH` at startup.
Restart the application after installing.

### ffmpeg

ffmpeg merges the separate video and audio streams and extracts audio. If a
system-wide ffmpeg is not found, the app falls back to the binary shipped with
`imageio-ffmpeg`, so no manual installation is normally required. Without any ffmpeg,
only pre-merged streams are available (usually capped around 720p) and audio
extraction is disabled.

## Usage

### Graphical interface

```bash
python yt_playlist_gui.py
```

1. Paste a playlist or video URL and click **Analyze** (or press Enter).
2. Uncheck the videos you do not want.
3. Choose a quality and an output folder.
4. Click **Download selection** and follow the progress.

Keyboard: `Enter` in the URL field analyzes; `Space` toggles the highlighted row.

### Command line

```bash
python yt_playlist.py
```

Paste a URL, press Enter, and the script downloads the whole playlist, then asks
for the next one. Type `q`, `quit`, `exit`, or submit an empty line to leave.
Settings live at the top of `yt_playlist.py` (`QUALITY`, `OUTPUT_DIR`, `COOKIES_FILE`,
`COOKIES_FROM_BROWSER`, `FORCE_AAC`); console messages are in French.

## Options reference (GUI)

| Option | Purpose |
| --- | --- |
| Quality | Maximum video height, or audio-only extraction (MP3 / M4A). |
| Folder | Root output folder. Defaults to `~/Downloads/yt_playlist`. |
| AAC audio | Re-encode audio to AAC 192 kbps during the merge, for players that cannot decode Opus (silent files). Applies to video downloads only. |
| Cookies file | Path to a `cookies.txt` exported with a browser extension such as "Get cookies.txt locally". |
| Browser cookies | Read cookies directly from Edge, Chrome, Firefox, Brave, Opera or Safari. The browser must be fully closed. |

Leave both cookie options empty to begin with; they are rarely needed once Deno is installed.
Use them for age-restricted or private videos.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `HTTP Error 403: Forbidden` | Deno is missing or not on `PATH` (red **Deno** badge). Install it and restart the app. |
| Downloads capped at 720p | ffmpeg not found (red **ffmpeg** badge). Run `pip install -U imageio-ffmpeg`. |
| Video plays without sound | Opus audio. Tick **AAC audio** (or set `FORCE_AAC = True` in the CLI). |
| `Sign in to confirm your age` | Provide cookies (file or browser). |
| Analysis fails or finds no video | Check the URL is a public or unlisted playlist/video; see the **Log** tab for the reason. |
| Some videos show *Error* | They failed and were skipped on purpose. The **Log** tab explains why; re-run to retry only those. |
| Extraction errors after a YouTube change | Update yt-dlp: `pip install -U --pre "yt-dlp[default]"`. |
| `No module named '_tkinter'` | Install Tkinter: `sudo apt install python3-tk` (Debian/Ubuntu). |

## Project layout

```
yt_playlist_gui.py   Graphical interface (Tkinter)
yt_playlist.py       Command-line version
requirements.txt     Python dependencies
README.md            This file (English)
README.fr.md         French version
```

## Legal

This tool is intended for downloading content you own, content published under a
permissive license, or content you have permission to download. Downloading
copyrighted material without authorization may violate YouTube's Terms of Service
and the copyright law of your jurisdiction. You are responsible for how you use it.

## License

Choose a license for your repository (MIT is a common default) and add it here
along with a `LICENSE` file.
