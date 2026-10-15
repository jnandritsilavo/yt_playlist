#!/usr/bin/env python3
"""
yt_playlist_gui.py — YT Playlist Pro : interface graphique professionnelle.
yt_playlist_gui.py — YT Playlist Pro: professional graphical interface.

  FR :
  • Analyse une playlist ou une vidéo, affiche la liste avec cases à cocher.
  • Qualité au choix (jusqu'à 4K) ou audio seul (MP3 / M4A).
  • Progression par vidéo et globale, vitesse, temps restant, annulation.
  • Thème sombre / clair, interface FR / EN, réglages mémorisés.
  • Même moteur que le script en ligne de commande (yt-dlp + ffmpeg + Deno).

  EN:
  • Analyzes a playlist or a video and lists it with checkboxes.
  • Selectable quality (up to 4K) or audio only (MP3 / M4A).
  • Per-video and global progress, speed, ETA, cancellation.
  • Dark / light theme, FR / EN interface, persistent settings.
  • Same engine as the command-line script (yt-dlp + ffmpeg + Deno).

Lancement / Run :
    python yt_playlist_gui.py
"""

from __future__ import annotations

import json
import os
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    import yt_dlp
    from yt_dlp.utils import sanitize_filename
except ImportError:
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "YT Playlist Pro",
        'Module manquant / Missing module.\n\n'
        'pip install -U --pre "yt-dlp[default]" imageio-ffmpeg',
    )
    sys.exit(1)

APP_NAME = "YT Playlist Pro"
APP_VERSION = "2.0"
CONFIG_PATH = Path.home() / ".yt_playlist_pro.json"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

QUALITY_VALUES = ["best", "2160", "1440", "1080", "720", "480", "360", "mp3", "m4a"]
QUALITY_KEYS = ["q_best", "q_2160", "q_1440", "q_1080", "q_720", "q_480", "q_360", "q_mp3", "q_m4a"]
BROWSERS = ["edge", "chrome", "firefox", "brave", "opera", "safari"]
URL_RE = re.compile(r"^https?://\S+$")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

DEFAULTS = {
    "quality": "1080",
    "output_dir": str(Path.home() / "Downloads" / "yt_playlist"),
    "force_aac": False,
    "cookies_file": "",
    "cookies_browser": "",
    "lang": "fr",
    "theme": "dark",
    "geometry": "1060x840",
}

# ═══════════════════════════ Traductions / Translations ═══════════════════════════
TEXT = {
    "fr": {
        "subtitle": "Téléchargeur de playlists YouTube en HD",
        "source": "SOURCE",
        "url_label": "URL de la playlist ou de la vidéo",
        "paste": "Coller",
        "analyse": "Analyser",
        "options": "OPTIONS",
        "quality": "Qualité",
        "folder": "Dossier",
        "browse": "Parcourir…",
        "force_aac": "Audio AAC (compatibilité maximale)",
        "cookies_file": "Fichier cookies",
        "cookies_browser": "Cookies navigateur",
        "none": "Aucun",
        "tab_queue": "  File d'attente  ",
        "tab_log": "  Journal  ",
        "col_n": "N°",
        "col_title": "Titre",
        "col_dur": "Durée",
        "col_status": "État",
        "sel_all": "Tout cocher",
        "sel_none": "Tout décocher",
        "sel_invert": "Inverser",
        "selected_count": "{n} / {total} sélectionnée(s)",
        "download": "Télécharger la sélection",
        "cancel": "Annuler",
        "open_folder": "Ouvrir le dossier",
        "current": "Vidéo en cours",
        "global": "Progression globale",
        "clear_log": "Effacer le journal",
        "idle": "Prêt.",
        "analysing": "Analyse en cours…",
        "info_empty": "Collez une URL puis cliquez sur Analyser.",
        "info_playlist": "Playlist « {title} » · {n} vidéo(s) · {dur}",
        "info_single": "Vidéo « {title} » · {dur}",
        "info_error": "Échec de l'analyse : {msg}",
        "err_url": "Veuillez saisir une URL valide (http:// ou https://).",
        "err_none": "Aucune vidéo sélectionnée.",
        "err_ffmpeg_audio": "ffmpeg est requis pour extraire l'audio.\n\npip install -U imageio-ffmpeg",
        "err_folder": "Dossier de sortie invalide :\n{msg}",
        "q_best": "Meilleure qualité",
        "q_2160": "4K · 2160p",
        "q_1440": "2K · 1440p",
        "q_1080": "Full HD · 1080p",
        "q_720": "HD · 720p",
        "q_480": "480p",
        "q_360": "360p",
        "q_mp3": "Audio MP3 (192 kbps)",
        "q_m4a": "Audio M4A (AAC)",
        "st_wait": "En attente",
        "st_run": "Téléchargement",
        "st_proc": "Traitement…",
        "st_done": "Terminé",
        "st_err": "Erreur",
        "st_cancel": "Annulé",
        "running_item": "Vidéo {k}/{n} · {title}",
        "cancelling": "Annulation en cours…",
        "finished": "Terminé : {ok} réussie(s), {ko} échec(s), {cx} annulée(s).",
        "confirm_quit": "Un téléchargement est en cours. Quitter quand même ?",
        "deps_title": "Dépendances",
        "ffmpeg_help": (
            "ffmpeg fusionne l'image et le son.\n\n"
            "Installez-le avec :\n    pip install -U imageio-ffmpeg\n\n"
            "Sans ffmpeg, la qualité est limitée à un fichier déjà fusionné (≈ 720p)\n"
            "et l'extraction audio est indisponible."
        ),
        "deno_help": (
            "Deno est requis par YouTube (erreurs HTTP 403 sinon).\n\n"
            "Windows :\n    winget install DenoLand.Deno\n"
            "    ou : irm https://deno.land/install.ps1 | iex\n\n"
            "macOS / Linux :\n    curl -fsSL https://deno.land/install.sh | sh\n\n"
            "Rouvrez ensuite l'application. Vous pouvez aussi poser deno(.exe)\n"
            "dans le dossier du script."
        ),
        "deps_ok": "Tout est en ordre.",
        "log_started": "Téléchargement de {n} vidéo(s) → {path}",
        "log_item_err": "Échec #{idx} : {msg}",
    },
    "en": {
        "subtitle": "HD YouTube playlist downloader",
        "source": "SOURCE",
        "url_label": "Playlist or video URL",
        "paste": "Paste",
        "analyse": "Analyze",
        "options": "OPTIONS",
        "quality": "Quality",
        "folder": "Folder",
        "browse": "Browse…",
        "force_aac": "AAC audio (maximum compatibility)",
        "cookies_file": "Cookies file",
        "cookies_browser": "Browser cookies",
        "none": "None",
        "tab_queue": "  Queue  ",
        "tab_log": "  Log  ",
        "col_n": "#",
        "col_title": "Title",
        "col_dur": "Duration",
        "col_status": "Status",
        "sel_all": "Select all",
        "sel_none": "Select none",
        "sel_invert": "Invert",
        "selected_count": "{n} / {total} selected",
        "download": "Download selection",
        "cancel": "Cancel",
        "open_folder": "Open folder",
        "current": "Current video",
        "global": "Overall progress",
        "clear_log": "Clear log",
        "idle": "Ready.",
        "analysing": "Analyzing…",
        "info_empty": "Paste a URL, then click Analyze.",
        "info_playlist": "Playlist “{title}” · {n} video(s) · {dur}",
        "info_single": "Video “{title}” · {dur}",
        "info_error": "Analysis failed: {msg}",
        "err_url": "Please enter a valid URL (http:// or https://).",
        "err_none": "No video selected.",
        "err_ffmpeg_audio": "ffmpeg is required to extract audio.\n\npip install -U imageio-ffmpeg",
        "err_folder": "Invalid output folder:\n{msg}",
        "q_best": "Best available",
        "q_2160": "4K · 2160p",
        "q_1440": "2K · 1440p",
        "q_1080": "Full HD · 1080p",
        "q_720": "HD · 720p",
        "q_480": "480p",
        "q_360": "360p",
        "q_mp3": "Audio MP3 (192 kbps)",
        "q_m4a": "Audio M4A (AAC)",
        "st_wait": "Waiting",
        "st_run": "Downloading",
        "st_proc": "Processing…",
        "st_done": "Done",
        "st_err": "Error",
        "st_cancel": "Cancelled",
        "running_item": "Video {k}/{n} · {title}",
        "cancelling": "Cancelling…",
        "finished": "Finished: {ok} succeeded, {ko} failed, {cx} cancelled.",
        "confirm_quit": "A download is in progress. Quit anyway?",
        "deps_title": "Dependencies",
        "ffmpeg_help": (
            "ffmpeg merges video and audio.\n\n"
            "Install it with:\n    pip install -U imageio-ffmpeg\n\n"
            "Without ffmpeg, quality is limited to a pre-merged file (≈ 720p)\n"
            "and audio extraction is unavailable."
        ),
        "deno_help": (
            "Deno is required by YouTube (HTTP 403 errors otherwise).\n\n"
            "Windows:\n    winget install DenoLand.Deno\n"
            "    or: irm https://deno.land/install.ps1 | iex\n\n"
            "macOS / Linux:\n    curl -fsSL https://deno.land/install.sh | sh\n\n"
            "Then restart the application. You can also drop deno(.exe)\n"
            "in the script folder."
        ),
        "deps_ok": "Everything is in order.",
        "log_started": "Downloading {n} video(s) → {path}",
        "log_item_err": "Failed #{idx}: {msg}",
    },
}

# ═══════════════════════════ Thèmes / Themes ═══════════════════════════
PALETTES = {
    "dark": dict(
        bg="#0e1117", surface="#171b24", surface2="#212736", border="#2d3445",
        fg="#e8ebf2", muted="#8c94a8", accent="#4f8cff", accent_fg="#ffffff",
        ok="#3ecf8e", err="#ff6b6b", warn="#f5b84b",
    ),
    "light": dict(
        bg="#f1f3f8", surface="#ffffff", surface2="#eaeef6", border="#d3d9e6",
        fg="#1a2030", muted="#667085", accent="#2f6df0", accent_fg="#ffffff",
        ok="#12905a", err="#d92d20", warn="#b54708",
    ),
}


def shade(hex_color: str, factor: float) -> str:
    """Éclaircit (>1) ou assombrit (<1) une couleur hexadécimale."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: max(0, min(255, int(c * factor)))  # noqa: E731
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"


# ═══════════════════════════ Utilitaires / Helpers ═══════════════════════════
def clean(text: str) -> str:
    return ANSI_RE.sub("", str(text)).strip()


def fmt_dur(sec) -> str:
    if not sec:
        return "—"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def fmt_speed(bps) -> str:
    if not bps:
        return "—"
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if bps < 1024:
            return f"{bps:.1f} {unit}"
        bps /= 1024
    return f"{bps:.1f} TB/s"


def fmt_eta(eta) -> str:
    if eta is None:
        return "—"
    return fmt_dur(max(int(eta), 0)) if eta >= 1 else "0:00"


def ensure_local_tools_on_path() -> None:
    """Rend trouvables deno / ffmpeg posés à côté du script. / Makes local binaries discoverable."""
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


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return cfg


def save_config(cfg: dict) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def open_in_file_manager(path: str) -> None:
    try:
        if IS_WIN:
            os.startfile(path)  # type: ignore[attr-defined]  # noqa: S606
        elif IS_MAC:
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# Exception d'annulation / Cancellation exception
Cancelled = getattr(yt_dlp.utils, "DownloadCancelled", None) or type("Cancelled", (Exception,), {})


class QLogger:
    """Logger yt-dlp → file d'événements de l'interface. / yt-dlp logger → UI event queue."""

    def __init__(self, q: queue.Queue):
        self.q = q

    def debug(self, msg):
        msg = clean(msg)
        if not msg or msg.startswith("[debug]"):
            return
        if msg.startswith("[download]") and "%" in msg:
            return  # la progression passe par les hooks / progress goes through hooks
        self.q.put(("log", "info", msg))

    info = debug

    def warning(self, msg):
        self.q.put(("log", "warn", clean(msg)))

    def error(self, msg):
        self.q.put(("log", "err", clean(msg)))


def format_selector(quality: str, has_ffmpeg: bool) -> str:
    h = "" if quality == "best" else f"[height<={quality}]"
    if not has_ffmpeg:
        return f"best{h}[ext=mp4][acodec!=none][vcodec!=none]/best{h}[acodec!=none][vcodec!=none]/best"
    return (
        f"bestvideo{h}[ext=mp4]+bestaudio[ext=m4a]/"
        f"bestvideo{h}+bestaudio[ext=m4a]/"
        f"bestvideo{h}+bestaudio/"
        f"best{h}/best"
    )


def base_opts(s: dict, logger) -> dict:
    """Options communes (cookies, logger). / Shared options (cookies, logger)."""
    opts = {"logger": logger, "quiet": True, "no_color": True}
    if s.get("cookies_file"):
        opts["cookiefile"] = s["cookies_file"]
    elif s.get("cookies_browser"):
        opts["cookiesfrombrowser"] = (s["cookies_browser"],)
    return opts


# ═══════════════════════════ Application ═══════════════════════════
class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = load_config()
        self.lang = self.cfg["lang"] if self.cfg["lang"] in TEXT else "fr"
        self.theme = self.cfg["theme"] if self.cfg["theme"] in PALETTES else "dark"

        ensure_local_tools_on_path()
        self.ffmpeg = find_ffmpeg()
        self.has_deno = bool(shutil.which("deno"))

        self.q: queue.Queue = queue.Queue()
        self.cancel_evt = threading.Event()
        self.worker: threading.Thread | None = None
        self.busy_analyse = False

        self.entries: list[dict] = []
        self.playlist = {"title": "", "is_playlist": False, "url": ""}
        self.i18n: list[tuple] = []          # (widget, key) à retraduire
        self.combos: list[ttk.Combobox] = []

        self.info_state: tuple = ("empty",)
        self.status_state: tuple = ("idle", {})
        self.total_jobs = 0
        self.done_count = 0
        self.cur_pct = 0.0

        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        base = tkfont.nametofont("TkDefaultFont").actual()["family"]
        self.font_family = "Segoe UI" if IS_WIN else ("Helvetica Neue" if IS_MAC else base)

        self._build()
        self.apply_theme()
        self.retranslate()

        root.protocol("WM_DELETE_WINDOW", self.on_close)
        root.after(100, self._poll)
        root.bind("<FocusIn>", self._maybe_autofill, add="+")
        self._maybe_autofill()
        if not self.ffmpeg:
            self.log("warn", "ffmpeg introuvable / not found → pip install -U imageio-ffmpeg")
        if not self.has_deno:
            self.log("warn", "Deno introuvable / not found → HTTP 403 probable (cliquer sur le badge / click the badge)")

    # ───────────── i18n ─────────────
    def L(self, key: str, **kw) -> str:
        table = TEXT.get(self.lang, TEXT["fr"])
        txt = table.get(key) or TEXT["fr"].get(key, key)
        return txt.format(**kw) if kw else txt

    def reg(self, widget, key: str):
        """Enregistre un widget dont le texte suit la langue. / Registers a language-aware widget."""
        self.i18n.append((widget, key))
        return widget

    # ───────────── Construction de l'interface ─────────────
    def _build(self):
        root = self.root
        root.title(f"{APP_NAME}")
        root.minsize(900, 720)
        try:
            root.geometry(self.cfg.get("geometry", DEFAULTS["geometry"]))
        except tk.TclError:
            root.geometry(DEFAULTS["geometry"])

        main = ttk.Frame(root, padding=(22, 18, 22, 10))
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(3, weight=1)
        self.main = main

        # ── En-tête / Header
        header = ttk.Frame(main)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        titles = ttk.Frame(header)
        titles.grid(row=0, column=0, sticky="w")
        ttk.Label(titles, text=f"▶  {APP_NAME}", style="Title.TLabel").pack(anchor="w")
        self.reg(ttk.Label(titles, style="Muted.TLabel"), "subtitle").pack(anchor="w")

        tools = ttk.Frame(header)
        tools.grid(row=0, column=1, sticky="e")
        self.badge_ffmpeg = ttk.Label(tools, cursor="hand2")
        self.badge_ffmpeg.pack(side="left", padx=(0, 6))
        self.badge_ffmpeg.bind("<Button-1>", lambda e: self.show_deps("ffmpeg_help"))
        self.badge_deno = ttk.Label(tools, cursor="hand2")
        self.badge_deno.pack(side="left", padx=(0, 14))
        self.badge_deno.bind("<Button-1>", lambda e: self.show_deps("deno_help"))
        self.btn_theme = ttk.Button(tools, width=3, command=self.toggle_theme)
        self.btn_theme.pack(side="left", padx=(0, 8))
        self.cb_lang = ttk.Combobox(tools, values=["Français", "English"], state="readonly", width=9)
        self.cb_lang.current(0 if self.lang == "fr" else 1)
        self.cb_lang.bind("<<ComboboxSelected>>", self.on_lang)
        self.cb_lang.pack(side="left")
        self.combos.append(self.cb_lang)

        # ── Carte Source / Source card
        src = ttk.Frame(main, style="Card.TFrame", padding=16)
        src.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        src.columnconfigure(0, weight=1)
        self.reg(ttk.Label(src, style="CardTitle.TLabel"), "source").grid(row=0, column=0, sticky="w")
        self.url_var = tk.StringVar()
        row = ttk.Frame(src, style="Card.TFrame")
        row.grid(row=1, column=0, sticky="ew", pady=(8, 6))
        row.columnconfigure(0, weight=1)
        self.ent_url = ttk.Entry(row, textvariable=self.url_var, font=(self.font_family, 11))
        self.ent_url.grid(row=0, column=0, sticky="ew", ipady=4)
        self.ent_url.bind("<Return>", lambda e: self.analyse())
        self.btn_paste = self.reg(ttk.Button(row, command=self.paste), "paste")
        self.btn_paste.grid(row=0, column=1, padx=(8, 0))
        self.btn_analyse = self.reg(ttk.Button(row, style="Accent.TButton", command=self.analyse), "analyse")
        self.btn_analyse.grid(row=0, column=2, padx=(8, 0))
        self.lbl_info = ttk.Label(src, style="CardMuted.TLabel")
        self.lbl_info.grid(row=2, column=0, sticky="w")

        # ── Carte Options / Options card
        opt = ttk.Frame(main, style="Card.TFrame", padding=16)
        opt.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        opt.columnconfigure(3, weight=1)
        self.reg(ttk.Label(opt, style="CardTitle.TLabel"), "options").grid(row=0, column=0, columnspan=5, sticky="w")

        self.reg(ttk.Label(opt, style="Card.TLabel"), "quality").grid(row=1, column=0, sticky="w", pady=(10, 0))
        self.cb_quality = ttk.Combobox(opt, state="readonly", width=22)
        self.cb_quality.grid(row=1, column=1, sticky="w", padx=(10, 24), pady=(10, 0))
        self.combos.append(self.cb_quality)

        self.reg(ttk.Label(opt, style="Card.TLabel"), "folder").grid(row=1, column=2, sticky="w", pady=(10, 0))
        self.outdir_var = tk.StringVar(value=self.cfg["output_dir"])
        ttk.Entry(opt, textvariable=self.outdir_var).grid(row=1, column=3, sticky="ew", padx=(10, 8), pady=(10, 0))
        self.reg(ttk.Button(opt, command=self.browse_dir), "browse").grid(row=1, column=4, pady=(10, 0))

        self.aac_var = tk.BooleanVar(value=bool(self.cfg["force_aac"]))
        self.reg(ttk.Checkbutton(opt, variable=self.aac_var, style="Card.TCheckbutton"), "force_aac").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(12, 0))

        adv = ttk.Frame(opt, style="Card.TFrame")
        adv.grid(row=2, column=2, columnspan=3, sticky="ew", pady=(10, 0))
        adv.columnconfigure(1, weight=1)
        self.reg(ttk.Label(adv, style="Card.TLabel"), "cookies_file").grid(row=0, column=0, sticky="w")
        self.cookies_var = tk.StringVar(value=self.cfg["cookies_file"])
        ttk.Entry(adv, textvariable=self.cookies_var).grid(row=0, column=1, sticky="ew", padx=(10, 8))
        ttk.Button(adv, text="…", width=3, command=self.browse_cookies).grid(row=0, column=2, padx=(0, 14))
        self.reg(ttk.Label(adv, style="Card.TLabel"), "cookies_browser").grid(row=0, column=3, sticky="w")
        self.cb_browser = ttk.Combobox(adv, state="readonly", width=10)
        self.cb_browser.grid(row=0, column=4, padx=(10, 0))
        self.combos.append(self.cb_browser)

        # ── Onglets / Tabs
        self.nb = ttk.Notebook(main)
        self.nb.grid(row=3, column=0, sticky="nsew", pady=(0, 10))

        tab_q = ttk.Frame(self.nb, style="Card.TFrame", padding=(12, 10, 12, 12))
        tab_q.columnconfigure(0, weight=1)
        tab_q.rowconfigure(1, weight=1)
        self.nb.add(tab_q, text="queue")
        bar = ttk.Frame(tab_q, style="Card.TFrame")
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.reg(ttk.Button(bar, command=lambda: self.select_all(True)), "sel_all").pack(side="left")
        self.reg(ttk.Button(bar, command=lambda: self.select_all(False)), "sel_none").pack(side="left", padx=6)
        self.reg(ttk.Button(bar, command=self.select_invert), "sel_invert").pack(side="left")
        self.lbl_count = ttk.Label(bar, style="CardMuted.TLabel")
        self.lbl_count.pack(side="right")

        cols = ("sel", "n", "title", "dur", "status")
        self.tree = ttk.Treeview(tab_q, columns=cols, show="headings", selectmode="browse", height=6)
        self.tree.column("sel", width=46, anchor="center", stretch=False)
        self.tree.column("n", width=56, anchor="center", stretch=False)
        self.tree.column("title", width=420, anchor="w")
        self.tree.column("dur", width=84, anchor="e", stretch=False)
        self.tree.column("status", width=215, anchor="w", stretch=False)
        self.tree.heading("sel", text="")
        vsb = ttk.Scrollbar(tab_q, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<space>", self.on_tree_space)

        tab_l = ttk.Frame(self.nb, style="Card.TFrame", padding=(12, 10, 12, 12))
        tab_l.columnconfigure(0, weight=1)
        tab_l.rowconfigure(1, weight=1)
        self.nb.add(tab_l, text="log")
        lbar = ttk.Frame(tab_l, style="Card.TFrame")
        lbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        self.reg(ttk.Button(lbar, command=self.clear_log), "clear_log").pack(side="right")
        self.txt_log = tk.Text(tab_l, height=6, wrap="word", relief="flat", borderwidth=0,
                               highlightthickness=0, state="disabled", padx=10, pady=8,
                               font=("Consolas" if IS_WIN else "Menlo" if IS_MAC else "DejaVu Sans Mono", 9))
        lsb = ttk.Scrollbar(tab_l, orient="vertical", command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=lsb.set)
        self.txt_log.grid(row=1, column=0, sticky="nsew")
        lsb.grid(row=1, column=1, sticky="ns")

        # ── Carte Progression / Progress card
        prog = ttk.Frame(main, style="Card.TFrame", padding=16)
        prog.grid(row=4, column=0, sticky="ew", pady=(0, 6))
        prog.columnconfigure(0, weight=1)

        top = ttk.Frame(prog, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        self.lbl_current = ttk.Label(top, style="Card.TLabel")
        self.lbl_current.grid(row=0, column=0, sticky="w")
        self.lbl_speed = ttk.Label(top, style="CardMuted.TLabel")
        self.lbl_speed.grid(row=0, column=1, sticky="e")
        self.bar_item = ttk.Progressbar(prog, style="Accent.Horizontal.TProgressbar", maximum=100)
        self.bar_item.grid(row=1, column=0, sticky="ew", pady=(6, 12))

        mid = ttk.Frame(prog, style="Card.TFrame")
        mid.grid(row=2, column=0, sticky="ew")
        mid.columnconfigure(0, weight=1)
        self.lbl_global = ttk.Label(mid, style="Card.TLabel")
        self.lbl_global.grid(row=0, column=0, sticky="w")
        self.lbl_global_pct = ttk.Label(mid, style="CardMuted.TLabel")
        self.lbl_global_pct.grid(row=0, column=1, sticky="e")
        self.bar_global = ttk.Progressbar(prog, style="Ok.Horizontal.TProgressbar", maximum=100)
        self.bar_global.grid(row=3, column=0, sticky="ew", pady=(6, 14))

        btns = ttk.Frame(prog, style="Card.TFrame")
        btns.grid(row=4, column=0, sticky="ew")
        btns.columnconfigure(2, weight=1)
        self.btn_dl = self.reg(ttk.Button(btns, style="Accent.TButton", command=self.start), "download")
        self.btn_dl.grid(row=0, column=0)
        self.btn_cancel = self.reg(ttk.Button(btns, style="Danger.TButton", command=self.cancel, state="disabled"), "cancel")
        self.btn_cancel.grid(row=0, column=1, padx=8)
        self.btn_open = self.reg(ttk.Button(btns, command=self.open_folder), "open_folder")
        self.btn_open.grid(row=0, column=3)

        # ── Pied de page / Footer
        foot = ttk.Frame(main)
        foot.grid(row=5, column=0, sticky="ew")
        foot.columnconfigure(0, weight=1)
        self.lbl_status = ttk.Label(foot, style="Muted.TLabel")
        self.lbl_status.grid(row=0, column=0, sticky="w")
        ttk.Label(foot, style="Muted.TLabel",
                  text=f"v{APP_VERSION} · yt-dlp {yt_dlp.version.__version__}").grid(row=0, column=1, sticky="e")

    # ───────────── Thème / Theme ─────────────
    def apply_theme(self):
        P = PALETTES[self.theme]
        s = self.style
        ff = self.font_family
        self.root.configure(background=P["bg"])

        s.configure(".", background=P["bg"], foreground=P["fg"], fieldbackground=P["surface2"],
                    bordercolor=P["border"], lightcolor=P["border"], darkcolor=P["border"],
                    troughcolor=P["surface2"], focuscolor=P["bg"], font=(ff, 10))
        s.configure("TFrame", background=P["bg"])
        s.configure("Card.TFrame", background=P["surface"])
        s.configure("TLabel", background=P["bg"], foreground=P["fg"])
        s.configure("Card.TLabel", background=P["surface"], foreground=P["fg"])
        s.configure("Muted.TLabel", background=P["bg"], foreground=P["muted"])
        s.configure("CardMuted.TLabel", background=P["surface"], foreground=P["muted"])
        s.configure("Title.TLabel", background=P["bg"], foreground=P["fg"], font=(ff, 20, "bold"))
        s.configure("CardTitle.TLabel", background=P["surface"], foreground=P["muted"], font=(ff, 9, "bold"))
        s.configure("BadgeOk.TLabel", background=P["surface2"], foreground=P["ok"], padding=(10, 4), font=(ff, 9, "bold"))
        s.configure("BadgeErr.TLabel", background=P["surface2"], foreground=P["err"], padding=(10, 4), font=(ff, 9, "bold"))

        s.configure("TButton", background=P["surface2"], foreground=P["fg"], bordercolor=P["border"],
                    lightcolor=P["surface2"], darkcolor=P["surface2"], padding=(14, 7), relief="flat", borderwidth=1)
        s.map("TButton", background=[("disabled", P["surface"]), ("active", P["border"])],
              foreground=[("disabled", P["muted"])])
        s.configure("Accent.TButton", background=P["accent"], foreground=P["accent_fg"], bordercolor=P["accent"],
                    lightcolor=P["accent"], darkcolor=P["accent"], padding=(18, 8), font=(ff, 10, "bold"))
        s.map("Accent.TButton", background=[("disabled", P["surface2"]), ("active", shade(P["accent"], 0.88))],
              foreground=[("disabled", P["muted"])], bordercolor=[("disabled", P["border"])])
        s.configure("Danger.TButton", background=P["surface2"], foreground=P["err"], bordercolor=P["border"],
                    lightcolor=P["surface2"], darkcolor=P["surface2"], padding=(16, 8))
        s.map("Danger.TButton", background=[("disabled", P["surface"]), ("active", P["border"])],
              foreground=[("disabled", P["muted"])])

        s.configure("TEntry", fieldbackground=P["surface2"], foreground=P["fg"], insertcolor=P["fg"],
                    bordercolor=P["border"], lightcolor=P["border"], darkcolor=P["border"], padding=6)
        s.map("TEntry", bordercolor=[("focus", P["accent"])], lightcolor=[("focus", P["accent"])],
              darkcolor=[("focus", P["accent"])])
        s.configure("TCombobox", fieldbackground=P["surface2"], background=P["surface2"], foreground=P["fg"],
                    arrowcolor=P["fg"], bordercolor=P["border"], lightcolor=P["border"], darkcolor=P["border"],
                    padding=5, selectbackground=P["surface2"], selectforeground=P["fg"])
        s.map("TCombobox", fieldbackground=[("readonly", P["surface2"])], foreground=[("readonly", P["fg"])],
              selectbackground=[("readonly", P["surface2"])], selectforeground=[("readonly", P["fg"])])
        s.configure("Card.TCheckbutton", background=P["surface"], foreground=P["fg"])
        s.map("Card.TCheckbutton", background=[("active", P["surface"])],
              indicatorcolor=[("selected", P["accent"]), ("!selected", P["surface2"])])

        s.configure("TNotebook", background=P["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))
        s.configure("TNotebook.Tab", background=P["bg"], foreground=P["muted"], padding=(14, 8), borderwidth=0,
                    bordercolor=P["bg"], lightcolor=P["bg"], darkcolor=P["bg"])
        s.map("TNotebook.Tab", background=[("selected", P["surface"])], foreground=[("selected", P["fg"])],
          bordercolor=[("selected", P["surface"])], lightcolor=[("selected", P["surface"])],
          darkcolor=[("selected", P["surface"])])

        s.configure("Treeview", background=P["surface"], fieldbackground=P["surface"], foreground=P["fg"],
                    rowheight=30, borderwidth=0, bordercolor=P["surface"])
        s.map("Treeview", background=[("selected", P["surface2"])], foreground=[("selected", P["fg"])])
        s.configure("Treeview.Heading", background=P["surface2"], foreground=P["muted"], relief="flat",
                    padding=(8, 6), font=(ff, 9, "bold"), borderwidth=0)
        s.map("Treeview.Heading", background=[("active", P["border"])])
        s.configure("Vertical.TScrollbar", background=P["surface2"], troughcolor=P["surface"],
                    bordercolor=P["surface"], arrowcolor=P["muted"], lightcolor=P["surface2"],
                    darkcolor=P["surface2"], gripcount=0)

        for name, colour in (("Accent", P["accent"]), ("Ok", P["ok"])):
            s.configure(f"{name}.Horizontal.TProgressbar", troughcolor=P["surface2"], background=colour,
                        bordercolor=P["surface"], lightcolor=colour, darkcolor=colour, thickness=10)

        self.tree.tag_configure("done", foreground=P["ok"])
        self.tree.tag_configure("err", foreground=P["err"])
        self.tree.tag_configure("run", foreground=P["accent"])
        self.tree.tag_configure("off", foreground=P["muted"])
        self.txt_log.configure(background=P["surface2"], foreground=P["fg"], insertbackground=P["fg"],
                               selectbackground=P["accent"])
        for tag, key in (("info", "fg"), ("warn", "warn"), ("err", "err"), ("ok", "ok")):
            self.txt_log.tag_configure(tag, foreground=P[key])

        for cb in self.combos:  # liste déroulante des combobox / combobox popdown list
            try:
                pop = self.root.tk.call("ttk::combobox::PopdownWindow", str(cb))
                self.root.tk.call(f"{pop}.f.l", "configure", "-background", P["surface2"], "-foreground", P["fg"],
                                  "-selectbackground", P["accent"], "-selectforeground", "#ffffff",
                                  "-borderwidth", 0, "-highlightthickness", 0)
            except tk.TclError:
                pass
        self.btn_theme.configure(text="☀" if self.theme == "dark" else "☾")
        self._refresh_badges()

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme()

    # ───────────── Langue / Language ─────────────
    def on_lang(self, _event=None):
        self.lang = "fr" if self.cb_lang.current() == 0 else "en"
        self.retranslate()

    def retranslate(self):
        for widget, key in self.i18n:
            widget.configure(text=self.L(key))
        for col, key in (("n", "col_n"), ("title", "col_title"), ("dur", "col_dur"), ("status", "col_status")):
            self.tree.heading(col, text=self.L(key))
        self.nb.tab(0, text=self.L("tab_queue"))
        self.nb.tab(1, text=self.L("tab_log"))

        qi = self.cb_quality.current()
        if qi < 0:
            qi = QUALITY_VALUES.index(self.cfg["quality"]) if self.cfg["quality"] in QUALITY_VALUES else 3
        self.cb_quality["values"] = [self.L(k) for k in QUALITY_KEYS]
        self.cb_quality.current(qi)

        bi = self.cb_browser.current()
        if bi < 0:
            bi = BROWSERS.index(self.cfg["cookies_browser"]) + 1 if self.cfg["cookies_browser"] in BROWSERS else 0
        self.cb_browser["values"] = [self.L("none")] + BROWSERS
        self.cb_browser.current(bi)

        self.btn_dl.configure(text=self.L("download"))
        self._render_info()
        self._render_count()
        self._render_status()
        self._refresh_badges()
        self._set_progress_labels_idle()
        for i in range(len(self.entries)):
            self._refresh_row(i)

    def _refresh_badges(self):
        self.badge_ffmpeg.configure(text=f"ffmpeg  {'✔' if self.ffmpeg else '✖'}",
                                    style="BadgeOk.TLabel" if self.ffmpeg else "BadgeErr.TLabel")
        self.badge_deno.configure(text=f"Deno  {'✔' if self.has_deno else '✖'}",
                                  style="BadgeOk.TLabel" if self.has_deno else "BadgeErr.TLabel")

    def show_deps(self, key: str):
        ok = self.ffmpeg if key == "ffmpeg_help" else self.has_deno
        messagebox.showinfo(self.L("deps_title"), self.L("deps_ok") if ok else self.L(key))

    # ───────────── Rendu des états / State rendering ─────────────
    def _render_info(self):
        st = self.info_state
        if st[0] == "empty":
            txt = self.L("info_empty")
        elif st[0] == "analysing":
            txt = self.L("analysing")
        elif st[0] == "playlist":
            txt = self.L("info_playlist", title=st[1], n=st[2], dur=st[3])
        elif st[0] == "single":
            txt = self.L("info_single", title=st[1], dur=st[2])
        else:
            txt = self.L("info_error", msg=st[1])
        self.lbl_info.configure(text=txt, foreground=PALETTES[self.theme]["err"] if st[0] == "error"
                                else PALETTES[self.theme]["muted"])

    def _render_count(self):
        n = sum(1 for e in self.entries if e["selected"])
        self.lbl_count.configure(text=self.L("selected_count", n=n, total=len(self.entries)))

    def set_status(self, key: str, **kw):
        self.status_state = (key, kw)
        self._render_status()

    def _render_status(self):
        key, kw = self.status_state
        self.lbl_status.configure(text=self.L(key, **kw))

    def _set_progress_labels_idle(self):
        if not self.is_running():
            self.lbl_current.configure(text=self.L("current"))
            self.lbl_global.configure(text=self.L("global"))
            self.lbl_global_pct.configure(text="")
            self.lbl_speed.configure(text="")

    def log(self, level: str, text: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", text + "\n", level)
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def clear_log(self):
        self.txt_log.configure(state="normal")
        self.txt_log.delete("1.0", "end")
        self.txt_log.configure(state="disabled")

    # ───────────── Presse-papier / Clipboard ─────────────
    def _maybe_autofill(self, event=None):
        if event is not None and event.widget is not self.root:
            return
        if self.url_var.get().strip() or self.is_running():
            return
        try:
            clip = self.root.clipboard_get().strip()
        except tk.TclError:
            return
        if URL_RE.match(clip) and re.search(r"(youtube\.com|youtu\.be)", clip):
            self.url_var.set(clip)

    def paste(self):
        try:
            clip = self.root.clipboard_get().strip()
        except tk.TclError:
            return
        self.url_var.set(clip)
        self.ent_url.focus_set()

    def browse_dir(self):
        d = filedialog.askdirectory(initialdir=self.outdir_var.get() or str(Path.home()))
        if d:
            self.outdir_var.set(d)

    def browse_cookies(self):
        f = filedialog.askopenfilename(filetypes=[("cookies.txt", "*.txt"), ("*", "*.*")])
        if f:
            self.cookies_var.set(f)

    # ───────────── Liste / Queue list ─────────────
    def _status_text(self, e: dict) -> tuple[str, str]:
        st = e["status"]
        if st == "run":
            return f"⬇  {self.L('st_run')} {e['pct']:.0f}%", "run"
        if st == "proc":
            return f"⚙  {self.L('st_proc')}", "run"
        if st == "done":
            return f"✔  {self.L('st_done')}", "done"
        if st == "err":
            return f"✖  {self.L('st_err')}", "err"
        if st == "cancel":
            return f"■  {self.L('st_cancel')}", "off"
        if st == "wait":
            return f"…  {self.L('st_wait')}", ""
        return "", "" if e["selected"] else "off"

    def _refresh_row(self, i: int):
        e = self.entries[i]
        text, tag = self._status_text(e)
        iid = str(i)
        if not self.tree.exists(iid):
            return
        self.tree.item(iid, tags=(tag,) if tag else ())
        self.tree.set(iid, "sel", "☑" if e["selected"] else "☐")
        self.tree.set(iid, "status", text)

    def _fill_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, e in enumerate(self.entries):
            self.tree.insert("", "end", iid=str(i),
                             values=("", f"{i + 1:02d}", e["title"], fmt_dur(e["duration"]), ""))
            self._refresh_row(i)
        self._render_count()

    def on_tree_click(self, event):
        if self.is_running():
            return
        if self.tree.identify_region(event.x, event.y) != "cell" or self.tree.identify_column(event.x) != "#1":
            return
        iid = self.tree.identify_row(event.y)
        if iid:
            self._toggle(int(iid))
            return "break"

    def on_tree_space(self, _event):
        sel = self.tree.selection()
        if sel and not self.is_running():
            self._toggle(int(sel[0]))
        return "break"

    def _toggle(self, i: int):
        self.entries[i]["selected"] = not self.entries[i]["selected"]
        self._refresh_row(i)
        self._render_count()

    def select_all(self, value: bool):
        if self.is_running():
            return
        for i, e in enumerate(self.entries):
            e["selected"] = value
            self._refresh_row(i)
        self._render_count()

    def select_invert(self):
        if self.is_running():
            return
        for i, e in enumerate(self.entries):
            e["selected"] = not e["selected"]
            self._refresh_row(i)
        self._render_count()

    # ───────────── Analyse ─────────────
    def snapshot(self) -> dict:
        """Capture les réglages (thread UI) pour les threads de travail. / Snapshot settings for workers."""
        qi = max(self.cb_quality.current(), 0)
        bi = self.cb_browser.current()
        return {
            "quality": QUALITY_VALUES[qi],
            "output_dir": self.outdir_var.get().strip(),
            "force_aac": bool(self.aac_var.get()),
            "cookies_file": self.cookies_var.get().strip(),
            "cookies_browser": BROWSERS[bi - 1] if bi > 0 else "",
        }

    def persist(self):
        s = self.snapshot()
        self.cfg.update(s)
        self.cfg.update({"lang": self.lang, "theme": self.theme, "geometry": self.root.geometry()})
        save_config(self.cfg)

    def is_running(self) -> bool:
        return bool(self.worker and self.worker.is_alive())

    def analyse(self):
        if self.is_running() or self.busy_analyse:
            return
        url = self.url_var.get().strip()
        if not URL_RE.match(url):
            messagebox.showwarning(APP_NAME, self.L("err_url"))
            return
        self.busy_analyse = True
        self.btn_analyse.configure(state="disabled")
        self.btn_dl.configure(state="disabled")
        self.info_state = ("analysing",)
        self._render_info()
        self.set_status("analysing")
        threading.Thread(target=self._analyse_worker, args=(url, self.snapshot()), daemon=True).start()

    def _analyse_worker(self, url: str, s: dict):
        opts = base_opts(s, QLogger(self.q))
        opts.update({"extract_flat": "in_playlist", "skip_download": True, "ignoreerrors": True})
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if not info:
                raise RuntimeError("no data")
            if info.get("entries") is not None:
                entries = []
                for e in info["entries"]:
                    if not e:
                        continue
                    eurl = e.get("url") or e.get("webpage_url")
                    if (not eurl or not str(eurl).startswith("http")) and e.get("id"):
                        eurl = f"https://www.youtube.com/watch?v={e['id']}"
                    if not eurl:
                        continue
                    entries.append({"url": eurl, "title": e.get("title") or e.get("id") or "?",
                                    "duration": e.get("duration")})
                result = {"is_playlist": True, "title": info.get("title") or "playlist", "entries": entries}
            else:
                result = {"is_playlist": False, "title": info.get("title") or "video",
                          "entries": [{"url": info.get("webpage_url") or url, "title": info.get("title") or "video",
                                       "duration": info.get("duration")}]}
            if not result["entries"]:
                raise RuntimeError("empty")
            result["url"] = url
            self.q.put(("analysed", result))
        except Exception as exc:  # noqa: BLE001
            self.q.put(("analyse_error", clean(str(exc))))

    # ───────────── Téléchargement / Download ─────────────
    def start(self):
        if self.is_running() or self.busy_analyse:
            return
        if not self.entries:
            if URL_RE.match(self.url_var.get().strip()):
                self.analyse()
            else:
                messagebox.showwarning(APP_NAME, self.L("err_url"))
            return
        jobs = [(i, e) for i, e in enumerate(self.entries) if e["selected"]]
        if not jobs:
            messagebox.showwarning(APP_NAME, self.L("err_none"))
            return
        s = self.snapshot()
        if s["quality"] in ("mp3", "m4a") and not self.ffmpeg:
            messagebox.showerror(APP_NAME, self.L("err_ffmpeg_audio"))
            return
        try:
            os.makedirs(s["output_dir"], exist_ok=True)
        except OSError as exc:
            messagebox.showerror(APP_NAME, self.L("err_folder", msg=exc))
            return
        self.persist()

        for i, e in enumerate(self.entries):
            e["status"] = "wait" if e["selected"] else ""
            e["pct"] = 0.0
            self._refresh_row(i)
        self.cancel_evt.clear()
        self.total_jobs, self.done_count, self.cur_pct = len(jobs), 0, 0.0
        self.bar_item["value"] = 0
        self.bar_global["value"] = 0
        self.lbl_global_pct.configure(text=f"0 / {len(jobs)}")
        self.btn_dl.configure(state="disabled")
        self.btn_analyse.configure(state="disabled")
        self.btn_cancel.configure(state="normal")
        self.set_status("idle")
        self.status_state = ("log_started", {"n": len(jobs), "path": s["output_dir"]})
        self._render_status()
        self.log("ok", self.L("log_started", n=len(jobs), path=s["output_dir"]))
        self.worker = threading.Thread(target=self._worker, args=(jobs, s, dict(self.playlist)), daemon=True)
        self.worker.start()

    def cancel(self):
        if self.is_running():
            self.cancel_evt.set()
            self.btn_cancel.configure(state="disabled")
            self.set_status("cancelling")

    def _target_dir(self, s: dict, playlist: dict) -> str:
        if playlist["is_playlist"]:
            return os.path.join(s["output_dir"], sanitize_filename(playlist["title"]) or "playlist")
        return s["output_dir"]

    def _worker(self, jobs, s, playlist):
        ok = ko = cx = 0
        total = len(jobs)
        target = self._target_dir(s, playlist)
        for k, (i, e) in enumerate(jobs, start=1):
            if self.cancel_evt.is_set():
                self.q.put(("item", i, "cancel", ""))
                cx += 1
                continue
            self.q.put(("item_start", i, k, total))
            res, msg = self._run_job(i, e, s, playlist, target)
            self.q.put(("item", i, res, msg))
            if res == "done":
                ok += 1
            elif res == "err":
                ko += 1
            else:
                cx += 1
        self.q.put(("finished", ok, ko, cx))

    def _run_job(self, i: int, entry: dict, s: dict, playlist: dict, target: str):
        idx = i + 1
        safe_target = target.replace("%", "%%")
        name = f"{idx:02d} - %(title)s.%(ext)s" if playlist["is_playlist"] else "%(title)s.%(ext)s"
        files: list[str] = []

        def hook(d):
            if self.cancel_evt.is_set():
                raise Cancelled("cancelled")
            fn = d.get("filename")
            if fn and fn not in files:
                files.append(fn)
            n = len((d.get("info_dict") or {}).get("requested_formats") or []) or 1
            si = min(max(len(files) - 1, 0), n - 1)
            if d.get("status") == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                frac = (d.get("downloaded_bytes") or 0) / total if total else 0.0
                pct = min((si + min(frac, 1.0)) / n * 100, 99.9)
                self.q.put(("progress", idx, pct, d.get("speed"), d.get("eta")))
            elif d.get("status") == "finished":
                self.q.put(("progress", idx, min((si + 1) / n * 100, 99.9), None, None))

        def pp_hook(d):
            if d.get("status") == "started":
                self.q.put(("phase", i))

        opts = base_opts(s, QLogger(self.q))
        audio_only = s["quality"] in ("mp3", "m4a")
        opts.update({
            "outtmpl": os.path.join(safe_target, name),
            "ignoreerrors": False,
            "noplaylist": True,
            "retries": 5,
            "fragment_retries": 5,
            "concurrent_fragment_downloads": 4,
            "trim_file_name": 180,
            "progress_hooks": [hook],
            "postprocessor_hooks": [pp_hook],
        })
        if self.ffmpeg:
            opts["ffmpeg_location"] = self.ffmpeg
        if audio_only:
            opts["format"] = "bestaudio[ext=m4a]/bestaudio/best" if s["quality"] == "m4a" else "bestaudio/best"
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": s["quality"],
                                       "preferredquality": "192"}]
        else:
            opts["format"] = format_selector(s["quality"], bool(self.ffmpeg))
            if self.ffmpeg:
                opts["merge_output_format"] = "mp4"
                if s["force_aac"]:
                    opts["postprocessor_args"] = {"merger": ["-c:a", "aac", "-b:a", "192k"]}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([entry["url"]])
            return "done", ""
        except Cancelled:
            return "cancel", ""
        except Exception as exc:  # noqa: BLE001
            if self.cancel_evt.is_set():
                return "cancel", ""
            return "err", clean(str(exc))

    # ───────────── Boucle d'événements UI / UI event loop ─────────────
    def _poll(self):
        try:
            while True:
                self._handle(self.q.get_nowait())
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _handle(self, ev: tuple):
        kind = ev[0]
        if kind == "log":
            self.log(ev[1], ev[2])

        elif kind == "analysed":
            r = ev[1]
            self.busy_analyse = False
            self.btn_analyse.configure(state="normal")
            self.btn_dl.configure(state="normal")
            self.playlist = {"title": r["title"], "is_playlist": r["is_playlist"], "url": r["url"]}
            self.entries = [{**e, "selected": True, "status": "", "pct": 0.0} for e in r["entries"]]
            total = sum(e["duration"] or 0 for e in self.entries)
            self.info_state = (("playlist", r["title"], len(self.entries), fmt_dur(total)) if r["is_playlist"]
                               else ("single", r["title"], fmt_dur(self.entries[0]["duration"])))
            self._render_info()
            self._fill_tree()
            self.nb.select(0)
            self.set_status("idle")

        elif kind == "analyse_error":
            self.busy_analyse = False
            self.btn_analyse.configure(state="normal")
            self.btn_dl.configure(state="normal")
            self.info_state = ("error", ev[1][:180])
            self._render_info()
            self.log("err", ev[1])
            self.set_status("idle")

        elif kind == "item_start":
            _, i, k, total = ev
            self.entries[i]["status"], self.entries[i]["pct"] = "run", 0.0
            self._refresh_row(i)
            if self.tree.exists(str(i)):
                self.tree.see(str(i))
            self.cur_pct = 0.0
            self.bar_item["value"] = 0
            self.lbl_current.configure(text=self.L("running_item", k=k, n=total, title=self.entries[i]["title"][:80]))
            self.lbl_speed.configure(text="")

        elif kind == "progress":
            _, idx, pct, speed, eta = ev
            i = idx - 1
            e = self.entries[i]
            if e["status"] not in ("run", "proc"):
                return
            e["status"], e["pct"] = "run", max(pct, e["pct"])
            self.cur_pct = e["pct"]
            self.bar_item["value"] = self.cur_pct
            self._refresh_row(i)
            if speed is not None or eta is not None:
                self.lbl_speed.configure(text=f"{fmt_speed(speed)}  ·  ETA {fmt_eta(eta)}")
            self._update_global()

        elif kind == "phase":
            i = ev[1]
            if self.entries[i]["status"] == "run":
                self.entries[i]["status"] = "proc"
                self._refresh_row(i)
                self.lbl_speed.configure(text=self.L("st_proc"))

        elif kind == "item":
            _, i, res, msg = ev
            e = self.entries[i]
            e["status"] = res
            if res == "done":
                e["pct"] = 100.0
                self.bar_item["value"] = 100
                self.done_count += 1
            elif res == "err":
                self.done_count += 1
                self.log("err", self.L("log_item_err", idx=i + 1, msg=msg))
            self.cur_pct = 0.0
            self._refresh_row(i)
            self._update_global()

        elif kind == "finished":
            _, ok, ko, cx = ev
            self.btn_dl.configure(state="normal")
            self.btn_analyse.configure(state="normal")
            self.btn_cancel.configure(state="disabled")
            self.lbl_current.configure(text=self.L("current"))
            self.lbl_speed.configure(text="")
            self.set_status("finished", ok=ok, ko=ko, cx=cx)
            self.log("ok" if ko == 0 else "warn", self.L("finished", ok=ok, ko=ko, cx=cx))
            if cx == 0:
                self.bar_global["value"] = 100
            self.root.bell()

    def _update_global(self):
        if not self.total_jobs:
            return
        pct = (self.done_count + self.cur_pct / 100) / self.total_jobs * 100
        self.bar_global["value"] = pct
        self.lbl_global_pct.configure(text=f"{self.done_count} / {self.total_jobs}  ·  {pct:.0f}%")

    # ───────────── Divers / Misc ─────────────
    def open_folder(self):
        s = self.snapshot()
        path = self._target_dir(s, self.playlist) if self.entries else s["output_dir"]
        if not os.path.isdir(path):
            path = s["output_dir"]
        if os.path.isdir(path):
            open_in_file_manager(path)

    def on_close(self):
        if self.is_running():
            if not messagebox.askyesno(APP_NAME, self.L("confirm_quit")):
                return
            self.cancel_evt.set()
        self.persist()
        self.root.destroy()


def main():
    if IS_WIN:
        try:  # netteté sur écrans HiDPI / crisp rendering on HiDPI screens
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
