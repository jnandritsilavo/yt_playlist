#!/usr/bin/env python3
"""
yt_playlist.py — Téléchargeur de playlists YouTube en HD (mode interactif).

  • Qualité HD (1080p) par défaut, image + son fusionnés en un seul MP4.
  • Numérotation 01, 02, 03… dans l'ordre de la playlist, rangée dans
    un dossier au nom de la playlist.
  • Demande l'URL, télécharge, puis redemande une autre URL en boucle.
  • Gère les blocages "HTTP 403" de YouTube (2026) via Deno.

PRÉREQUIS (à faire une fois, dans le terminal) :
    pip install -U --pre "yt-dlp[default]" imageio-ffmpeg
    + installer Deno (voir messages au démarrage si absent)

Lancement :
    python yt_playlist.py
"""

import os
import sys
import shutil

try:
    import yt_dlp
except ImportError:
    sys.exit('Module manquant. Faites :  pip install -U --pre "yt-dlp[default]" imageio-ffmpeg')

# ─────────── Réglages ───────────
QUALITY = 1080          # HD par défaut
OUTPUT_DIR = "downloads"

# Cookies — laissez les DEUX sur None pour commencer (souvent inutiles avec Deno).
# Si une vidéo précise reste bloquée (âge, privé), exportez un cookies.txt
# avec l'extension navigateur "Get cookies.txt locally" et indiquez son chemin ici.
COOKIES_FILE = None            # ex : r"H:\portfolio\cookies.txt"
COOKIES_FROM_BROWSER = None    # ex : "edge" — NÉCESSITE de fermer le navigateur

# Si une vidéo reste MUETTE (audio Opus que le lecteur Windows ne lit pas),
# passez ceci à True : l'audio sera ré-encodé en AAC, lu partout.
FORCE_AAC = False
# ─────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_local_tools_on_path():
    """Si deno.exe / ffmpeg.exe sont posés à côté du script, on les rend trouvables."""
    for folder in (SCRIPT_DIR, os.getcwd()):
        if folder and folder not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")


def find_ffmpeg():
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


ensure_local_tools_on_path()
FFMPEG = find_ffmpeg()


def build_opts():
    outtmpl = f"{OUTPUT_DIR}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"

    if FFMPEG:
        opts = {
            # Priorité : vidéo MP4 (H.264) + audio M4A (AAC) → son lu partout.
            # Repli sur d'autres combinaisons si indisponible.
            "format": (
                f"bestvideo[height<={QUALITY}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={QUALITY}]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={QUALITY}]+bestaudio/"
                f"best[height<={QUALITY}]/best"
            ),
            "merge_output_format": "mp4",
            "ffmpeg_location": FFMPEG,
        }
        if FORCE_AAC:
            # Ré-encode l'audio en AAC au moment de la fusion (compatibilité maximale).
            opts["postprocessor_args"] = {"merger": ["-c:a", "aac", "-b:a", "192k"]}
    else:
        opts = {
            "format": "best[ext=mp4][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]/best",
        }

    opts.update({
        "outtmpl": outtmpl,
        "ignoreerrors": True,
        "noplaylist": False,
        "sleep_interval_requests": 1,
        "retries": 5,
        "fragment_retries": 5,
    })

    if COOKIES_FILE:
        opts["cookiefile"] = COOKIES_FILE
    elif COOKIES_FROM_BROWSER:
        opts["cookiesfrombrowser"] = (COOKIES_FROM_BROWSER,)

    return opts


def download(url: str):
    with yt_dlp.YoutubeDL(build_opts()) as ydl:
        ydl.download([url])


def main():
    print("=" * 56)
    print("  Téléchargeur de playlists YouTube — HD (1080p)")
    print("=" * 56)

    if FFMPEG:
        print(f"ffmpeg détecté ✅   {FFMPEG}")
    else:
        print("⚠️  ffmpeg introuvable → pip install -U imageio-ffmpeg")

    if shutil.which("deno"):
        print("Deno détecté ✅   (signatures YouTube résolues)")
    else:
        print("⚠️  Deno INTROUVABLE — c'est la cause des erreurs HTTP 403.")
        print("    Essayez, dans l'ordre :")
        print("      1) winget install DenoLand.Deno")
        print("      2) PowerShell :  irm https://deno.land/install.ps1 | iex")
        print("      3) Manuel : télécharger deno.exe (github.com/denoland/deno/releases)")
        print("         puis le poser DANS le dossier de ce script.")
        print("    Rouvrez le terminal après installation.")

    cookies = COOKIES_FILE or COOKIES_FROM_BROWSER or "désactivés"
    print(f"Cookies : {cookies}")
    print("-" * 56)
    print("Collez une URL et Entrée. 'q' ou vide pour quitter.\n")

    while True:
        try:
            url = input("URL ▶  ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAu revoir.")
            break

        if url == "" or url.lower() in ("q", "quit", "exit"):
            print("Au revoir.")
            break

        print(f"\nTéléchargement → {OUTPUT_DIR}/\n")
        try:
            download(url)
            print("\n✅ Terminé.\n")
        except KeyboardInterrupt:
            print("\n⏹  Interrompu.\n")
        except Exception as exc:  # noqa: BLE001
            print(f"\n❌ Erreur : {exc}\n")

        print("-" * 56)
        print("Prêt pour une autre URL.\n")


if __name__ == "__main__":
    main()
