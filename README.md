# yt_playlist

An interactive command-line downloader for YouTube playlists, built on top of
[yt-dlp](https://github.com/yt-dlp/yt-dlp). It fetches every video of a playlist
in HD, merges video and audio into a single MP4, and names the files so they stay
in playlist order.

The script is a thin, opinionated wrapper: all the defaults that usually take a
long command line (format selection, output template, retries, ffmpeg location)
are already set.

## Features

- 1080p by default, with automatic fallback to the best available quality below that limit.
- Video and audio merged into one MP4 file via ffmpeg.
- Files numbered `01 - Title.mp4`, `02 - Title.mp4`, and so on, following the playlist order.
- Each playlist stored in its own folder, named after the playlist.
- Interactive loop: paste a URL, wait for the download, paste the next one.
- Resilient by design: a video that fails is skipped instead of aborting the whole playlist.
- Optional AAC re-encoding for players that cannot decode Opus audio.
- Optional cookie support for age-restricted or private videos.

## Requirements

- Python 3.8 or newer
- yt-dlp and imageio-ffmpeg (installed below)
- Deno, used to solve YouTube's JavaScript challenges

Install the Python dependencies:

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
same folder as the script; the script adds its own directory to `PATH` at startup.
Reopen your terminal after installing.

### ffmpeg

ffmpeg is used to merge the separate video and audio streams. If a system-wide
ffmpeg is not found, the script falls back to the binary shipped with
`imageio-ffmpeg`, so no manual installation is normally required. If neither is
available, the script still runs but downloads a single pre-muxed stream, which
usually caps quality at 720p.

## Usage

```bash
python yt_playlist.py
```

The script prints a short diagnostic (ffmpeg, Deno, cookies), then waits for input:

```
URL >  https://www.youtube.com/playlist?list=PL...
```

Press Enter to start. When the download finishes, the prompt returns for the next
URL. Type `q`, `quit`, `exit`, or submit an empty line to leave. `Ctrl+C` during a
download cancels that download only and returns to the prompt.

Single video URLs work too; they are simply treated as a playlist of one.

## Output layout

```
downloads/
  My Playlist Name/
    01 - First video.mp4
    02 - Second video.mp4
    03 - Third video.mp4
```

## Configuration

All settings live at the top of `yt_playlist.py`.

| Setting | Default | Purpose |
| --- | --- | --- |
| `QUALITY` | `1080` | Maximum height in pixels. Use `720`, `1440`, `2160`, and so on. |
| `OUTPUT_DIR` | `"downloads"` | Root folder for downloads, relative to the working directory. |
| `COOKIES_FILE` | `None` | Path to a `cookies.txt` file. |
| `COOKIES_FROM_BROWSER` | `None` | Browser name such as `"edge"` or `"firefox"`, read cookies directly. |
| `FORCE_AAC` | `False` | Re-encode audio to AAC during the merge. |

### Cookies

Leave both cookie settings on `None` to begin with. They are rarely needed once
Deno is installed. If one specific video stays blocked because it is age-restricted
or private, export a `cookies.txt` with a browser extension such as
"Get cookies.txt locally" and set `COOKIES_FILE` to its path.

Reading cookies directly from a browser with `COOKIES_FROM_BROWSER` requires the
browser to be fully closed, since the cookie database is locked while it runs.

### Silent video files

Some YouTube streams use the Opus audio codec, which older Windows players cannot
decode; the file plays but has no sound. Set `FORCE_AAC = True` to re-encode the
audio track to AAC at 192 kbps during the merge. This costs a little CPU time but
produces files that play everywhere.

## Troubleshooting

| Symptom | Likely cause and fix |
| --- | --- |
| `HTTP Error 403: Forbidden` | Deno is missing or not on `PATH`. Install it and reopen the terminal. |
| Downloads capped at 720p | ffmpeg was not found, so no separate streams could be merged. Run `pip install -U imageio-ffmpeg`. |
| Video plays without sound | Opus audio. Set `FORCE_AAC = True`. |
| `Sign in to confirm your age` | Provide cookies via `COOKIES_FILE`. |
| Some videos are missing from the folder | They failed and were skipped on purpose; scroll back through the log for the reason. |
| Extraction errors after a YouTube change | Update yt-dlp: `pip install -U --pre "yt-dlp[default]"`. |

## Notes

The console messages are in French; the source comments are bilingual
(English and French).

## Legal

This tool is intended for downloading content you own, content published under a
permissive license, or content you have permission to download. Downloading
copyrighted material without authorization may violate YouTube's Terms of Service
and the copyright law of your jurisdiction. You are responsible for how you use it.

## License

Choose a license for your repository (MIT is a common default) and add it here
along with a `LICENSE` file.
