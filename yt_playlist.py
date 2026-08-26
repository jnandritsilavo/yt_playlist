#!/usr/bin/env python3
"""
yt_playlist.py — YouTube playlist downloader in HD (interactive mode).
yt_playlist.py — Téléchargeur de playlists YouTube en HD (mode interactif).

  EN:
  • HD quality (1080p) by default, video + audio merged into a single MP4.
  • Numbering 01, 02, 03... following the playlist order, stored in
    a folder named after the playlist.
  • Asks for a URL, downloads it, then asks for another URL in a loop.
  • Handles YouTube "HTTP 403" blocks (2026) through Deno.

  FR:
  • Qualité HD (1080p) par défaut, image + son fusionnés en un seul MP4.
  • Numérotation 01, 02, 03… dans l'ordre de la playlist, rangée dans
    un dossier au nom de la playlist.
  • Demande l'URL, télécharge, puis redemande une autre URL en boucle.
  • Gère les blocages "HTTP 403" de YouTube (2026) via Deno.

REQUIREMENTS / PRÉREQUIS (once, in the terminal / à faire une fois, dans le terminal):
    pip install -U --pre "yt-dlp[default]" imageio-ffmpeg
    + install Deno (see startup messages if missing)
    + installer Deno (voir messages au démarrage si absent)

Run / Lancement :
    python yt_playlist.py
"""

import os
import sys
import shutil

try:
    import yt_dlp
except ImportError:
    sys.exit('Module manquant. Faites :  pip install -U --pre "yt-dlp[default]" imageio-ffmpeg')

# ─────────── Settings / Réglages ───────────
QUALITY = 1080          # EN: HD by default — FR: HD par défaut
OUTPUT_DIR = "downloads"

# EN: Cookies — leave BOTH on None to start with (often useless when Deno is present).
#     If one specific video stays blocked (age-restricted, private), export a cookies.txt
#     with the browser extension "Get cookies.txt locally" and put its path here.
# FR: Cookies — laissez les DEUX sur None pour commencer (souvent inutiles avec Deno).
#     Si une vidéo précise reste bloquée (âge, privé), exportez un cookies.txt
#     avec l'extension navigateur "Get cookies.txt locally" et indiquez son chemin ici.
COOKIES_FILE = None            # e.g. / ex : r"H:\portfolio\cookies.txt"
COOKIES_FROM_BROWSER = None    # e.g. / ex : "edge" — REQUIRES closing the browser
                               #                    — NÉCESSITE de fermer le navigateur

# EN: If a video ends up SILENT (Opus audio that the Windows player cannot read),
#     switch this to True: the audio will be re-encoded to AAC, playable everywhere.
# FR: Si une vidéo reste MUETTE (audio Opus que le lecteur Windows ne lit pas),
#     passez ceci à True : l'audio sera ré-encodé en AAC, lu partout.
FORCE_AAC = False
# ───────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def ensure_local_tools_on_path():
    """
    EN: If deno.exe / ffmpeg.exe sit next to the script, make them discoverable.
    FR: Si deno.exe / ffmpeg.exe sont posés à côté du script, on les rend trouvables.
    """
    for folder in (SCRIPT_DIR, os.getcwd()):
        if folder and folder not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = folder + os.pathsep + os.environ.get("PATH", "")


def find_ffmpeg():
    """
    EN: Return the path to ffmpeg: system install first, then the imageio-ffmpeg binary.
    FR: Renvoie le chemin de ffmpeg : installation système d'abord, sinon le binaire
        fourni par imageio-ffmpeg.
    """
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
    """
    EN: Build the yt-dlp options dictionary (format, output template, retries).
    FR: Construit le dictionnaire d'options de yt-dlp (format, modèle de nom, réessais).
    """
    outtmpl = f"{OUTPUT_DIR}/%(playlist_title)s/%(playlist_index)02d - %(title)s.%(ext)s"

    if FFMPEG:
        opts = {
            # EN: Priority: MP4 video (H.264) + M4A audio (AAC) → sound plays everywhere.
            #     Falls back to other combinations when unavailable.
            # FR: Priorité : vidéo MP4 (H.264) + audio M4A (AAC) → son lu partout.
            #     Repli sur d'autres combinaisons si indisponible.
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
            # EN: Re-encode the audio to AAC while merging (maximum compatibility).
            # FR: Ré-encode l'audio en AAC au moment de la fusion (compatibilité maximale).
            opts["postprocessor_args"] = {"merger": ["-c:a", "aac", "-b:a", "192k"]}
    else:
        # EN: No ffmpeg → take a single pre-muxed file (video and audio already together).
        # FR: Pas de ffmpeg → on prend un fichier déjà muxé (image et son ensemble).
        opts = {
            "format": "best[ext=mp4][acodec!=none][vcodec!=none]/best[acodec!=none][vcodec!=none]/best",
        }

    opts.update({
        "outtmpl": outtmpl,
        "ignoreerrors": True,          # EN: skip a failing video — FR: ignore une vidéo en échec
        "noplaylist": False,           # EN: keep the whole playlist — FR: garde toute la playlist
        "sleep_interval_requests": 1,  # EN: be gentle with YouTube — FR: ménage YouTube
        "retries": 5,
        "fragment_retries": 5,
    })

    if COOKIES_FILE:
        opts["cookiefile"] = COOKIES_FILE
    elif COOKIES_FROM_BROWSER:
        opts["cookiesfrombrowser"] = (COOKIES_FROM_BROWSER,)

    return opts


def download(url: str):
    """
    EN: Download the given playlist or video URL.
    FR: Télécharge l'URL de playlist ou de vidéo fournie.
    """
    with yt_dlp.YoutubeDL(build_opts()) as ydl:
        ydl.download([url])


def main():
    """
    EN: Startup diagnostics (ffmpeg, Deno, cookies), then the interactive URL loop.
    FR: Diagnostic de démarrage (ffmpeg, Deno, cookies), puis boucle interactive d'URL.
    """
    print("=" * 56)
    print("  Téléchargeur de playlists YouTube — HD (1080p)")
    print("=" * 56)

    # EN: ffmpeg is what merges the separate video and audio streams.
    # FR: ffmpeg est ce qui fusionne les flux vidéo et audio séparés.
    if FFMPEG:
        print(f"ffmpeg détecté ✅   {FFMPEG}")
    else:
        print("⚠️  ffmpeg introuvable → pip install -U imageio-ffmpeg")

    # EN: Deno runs YouTube's JS challenge; without it, expect HTTP 403 errors.
    # FR: Deno exécute le défi JS de YouTube ; sans lui, attendez-vous à des erreurs HTTP 403.
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

    # EN: Main loop — one URL per iteration, until the user quits.
    # FR: Boucle principale — une URL par tour, jusqu'à ce que l'utilisateur quitte.
    while True:
        try:
            url = input("URL ▶  ").strip()
        except (EOFError, KeyboardInterrupt):
            # EN: Ctrl+C or piped input exhausted → clean exit.
            # FR: Ctrl+C ou fin d'entrée redirigée → sortie propre.
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
            # EN: Ctrl+C during a download → cancel this one, keep the loop alive.
            # FR: Ctrl+C pendant un téléchargement → annule celui-ci, garde la boucle.
            print("\n⏹  Interrompu.\n")
        except Exception as exc:  # noqa: BLE001
            # EN: Never crash the loop on a single bad URL.
            # FR: Ne jamais faire planter la boucle à cause d'une seule mauvaise URL.
            print(f"\n❌ Erreur : {exc}\n")

        print("-" * 56)
        print("Prêt pour une autre URL.\n")


if __name__ == "__main__":
    main()
