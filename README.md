# YT Playlist Downloader

Petit outil en ligne de commande pour télécharger une playlist YouTube en HD.
Chaque vidéo est numérotée selon son ordre dans la playlist et rangée dans un
dossier portant le nom de la playlist. L'image et le son sont réunis dans un
seul fichier MP4.

```
downloads/
└── Nom de la playlist/
    ├── 01 - Première vidéo.mp4
    ├── 02 - Deuxième vidéo.mp4
    └── 03 - Troisième vidéo.mp4
```

## Ce que ça fait

- Téléchargement en 1080p par défaut (réglable).
- Numérotation 01, 02, 03… dans l'ordre exact de la playlist.
- Un dossier créé automatiquement par playlist.
- Image et son fusionnés dans un seul `.mp4`, avec un audio AAC lisible partout.
- Mode interactif : on colle une URL, ça télécharge, puis ça en redemande une
  autre, jusqu'à ce qu'on quitte.
- Gère les erreurs `HTTP 403` que YouTube renvoie depuis 2026 (via Deno).
- Trouve `ffmpeg` et `deno` tout seul, y compris s'ils sont posés à côté du script.

## Prérequis

- Python 3.10 ou plus récent
- yt-dlp (le moteur de téléchargement)
- ffmpeg (pour fusionner image et son)
- Deno (pour résoudre les signatures YouTube et éviter les erreurs 403)

## Installation

Installer Python et les paquets :

```bash
pip install -U --pre "yt-dlp[default]" imageio-ffmpeg
```

`imageio-ffmpeg` embarque un ffmpeg prêt à l'emploi. Si vous préférez un ffmpeg
système : `winget install Gyan.FFmpeg` sous Windows, `brew install ffmpeg` sous
macOS, `sudo apt install ffmpeg` sous Linux.

Installer Deno (obligatoire depuis 2026, sinon YouTube renvoie des erreurs 403) :

```bash
winget install DenoLand.Deno              # Windows, WinGet
irm https://deno.land/install.ps1 | iex   # Windows, PowerShell
curl -fsSL https://deno.land/install.sh | sh   # macOS / Linux
```

Si les installeurs sont bloqués (poste d'entreprise par exemple), téléchargez
`deno.exe` depuis les releases GitHub de Deno et posez-le directement dans le
dossier du script : il sera détecté automatiquement. Pensez à rouvrir le
terminal après l'installation.

## Utilisation

```bash
python yt_playlist.py
```

Au démarrage, le script affiche s'il a bien trouvé ffmpeg et Deno. Collez ensuite
une URL de playlist et appuyez sur Entrée. Une fois le téléchargement terminé, il
en redemande une autre. Tapez `q` ou laissez vide pour quitter.

```
URL ▶  https://www.youtube.com/playlist?list=XXXXXXXX
```

## Réglages

Les options se trouvent en haut de `yt_playlist.py` :

| Variable               | Défaut       | Description |
|------------------------|--------------|-------------|
| `QUALITY`              | `1080`       | Hauteur max en pixels (480, 720, 1080, 2160). |
| `OUTPUT_DIR`           | `"downloads"`| Dossier de destination. |
| `COOKIES_FILE`         | `None`       | Chemin d'un `cookies.txt` pour les vidéos privées ou avec limite d'âge. |
| `COOKIES_FROM_BROWSER` | `None`       | `"chrome"`, `"edge"`, `"firefox"`… Fermez le navigateur avant de lancer. |
| `FORCE_AAC`            | `False`      | Ré-encode l'audio en AAC si une vidéo reste muette. |

## Problèmes courants

**`HTTP Error 403: Forbidden`**
Deno n'est pas installé ou pas trouvé. Installez-le, rouvrez le terminal, et
mettez yt-dlp à jour avec `yt-dlp --update-to nightly`. Sur un réseau
d'entreprise, ce type de trafic est parfois filtré : testez depuis une connexion
personnelle pour en avoir le cœur net.

**Vidéo et audio téléchargés séparément**
ffmpeg est introuvable, or c'est lui qui fusionne les deux flux. Installez-le ou
faites `pip install -U imageio-ffmpeg`.

**Vidéo muette à la lecture**
L'audio est en Opus, que certains lecteurs Windows ne décodent pas dans un MP4.
Le script prend l'audio AAC en priorité pour éviter ça. Si une vidéo reste
muette, passez `FORCE_AAC` à `True`. Pour vérifier, ouvrez le fichier dans VLC :
s'il a du son là, c'était bien un souci de codec.

**`Could not copy Chrome cookie database`**
Le navigateur est ouvert et sa base de cookies est verrouillée. Fermez-le, ou
laissez `COOKIES_FROM_BROWSER` à `None` et utilisez plutôt un fichier `cookies.txt`
via `COOKIES_FILE`.

## Avertissement

À utiliser pour des contenus que vous avez le droit de récupérer : vos propres
vidéos, des contenus sous licence libre, ou avec l'accord de l'auteur. Respectez
les conditions d'utilisation de YouTube et le droit d'auteur en vigueur chez vous.

Construit autour de [yt-dlp](https://github.com/yt-dlp/yt-dlp) et
[ffmpeg](https://ffmpeg.org/).
