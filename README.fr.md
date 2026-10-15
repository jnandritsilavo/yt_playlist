# YT Playlist Pro

*[English version → README.md](README.md)*

Une application de bureau et un outil en ligne de commande pour télécharger des
playlists YouTube en HD, construits sur [yt-dlp](https://github.com/yt-dlp/yt-dlp).
Analysez une playlist, choisissez les vidéos voulues, sélectionnez une qualité et
suivez la progression dans une interface claire, en thème sombre ou clair.

Le projet fournit deux interfaces qui partagent le même moteur (yt-dlp + ffmpeg + Deno) :

| Fichier | Rôle |
| --- | --- |
| `yt_playlist_gui.py` | **Interface graphique (recommandée).** Aucune dépendance supplémentaire : utilise Tkinter, fourni avec Python. |
| `yt_playlist.py` | Version minimale en ligne de commande, inchangée. |

## Fonctionnalités

### Interface graphique

- **Analyse avant téléchargement** : liste toutes les vidéos de la playlist avec leur durée et la durée totale.
- **Sélection** : case à cocher par vidéo, plus *Tout cocher / Tout décocher / Inverser*.
- **Choix de qualité** : meilleure disponible, 4K, 2K, 1080p, 720p, 480p, 360p, ou **audio seul** (MP3 192 kbps / M4A).
- **Progression en direct** : barre par vidéo, barre globale, vitesse, temps restant et état de chaque ligne
  (en attente, téléchargement, traitement, terminé, erreur, annulé).
- **Annulation à tout moment**, sans geler la fenêtre ; une vidéo en échec n'arrête jamais les suivantes.
- **Thèmes sombre et clair**, interface **française et anglaise**, modifiables à la volée.
- **Réglages mémorisés** d'une session à l'autre (`~/.yt_playlist_pro.json`).
- **Pastilles d'état** pour ffmpeg et Deno ; un clic affiche l'aide d'installation.
- **Détection du presse-papiers** : un lien YouTube copié est pré-rempli à l'ouverture.
- Onglet journal intégré, bouton *Ouvrir le dossier*, audio AAC optionnel, cookies par fichier ou par navigateur.

### Résultat (les deux versions)

- Image et son fusionnés dans un seul fichier MP4 grâce à ffmpeg.
- Fichiers numérotés dans l'ordre de la playlist, numéro conservé même si vous ne
  sélectionnez qu'une partie des vidéos : `01 - Première vidéo.mp4`, `04 - Quatrième vidéo.mp4`…
- Un dossier par playlist, au nom de la playlist. Une vidéo seule est enregistrée directement dans le dossier de sortie.

## Prérequis

- Python 3.8 ou plus récent, avec Tkinter (inclus dans les installateurs officiels Windows et macOS ;
  sous Debian/Ubuntu : `sudo apt install python3-tk`)
- yt-dlp et imageio-ffmpeg
- Deno, utilisé pour résoudre les défis JavaScript de YouTube

```bash
pip install -r requirements.txt
```

ou, pour obtenir la dernière version de yt-dlp :

```bash
pip install -U --pre "yt-dlp[default]" imageio-ffmpeg
```

### Deno

Depuis 2026, YouTube exige un moteur JavaScript pour résoudre les signatures du lecteur.
Sans Deno, la plupart des téléchargements échouent avec `HTTP Error 403: Forbidden`.

Windows :

```powershell
winget install DenoLand.Deno
```

ou

```powershell
irm https://deno.land/install.ps1 | iex
```

macOS et Linux :

```bash
curl -fsSL https://deno.land/install.sh | sh
```

En dernier recours, téléchargez `deno.exe` depuis la
[page des versions de Deno](https://github.com/denoland/deno/releases) et posez-le dans
le même dossier que les scripts ; ils ajoutent leur propre dossier au `PATH` au démarrage.
Relancez l'application après l'installation.

### ffmpeg

ffmpeg fusionne les flux image et son séparés et extrait l'audio. Si aucun ffmpeg n'est
installé sur le système, l'application utilise le binaire fourni par `imageio-ffmpeg` :
aucune installation manuelle n'est normalement nécessaire. Sans ffmpeg, seuls les flux
déjà fusionnés sont disponibles (souvent limités à environ 720p) et l'extraction audio est désactivée.

## Utilisation

### Interface graphique

```bash
python yt_playlist_gui.py
```

1. Collez l'URL d'une playlist ou d'une vidéo, puis cliquez sur **Analyser** (ou appuyez sur Entrée).
2. Décochez les vidéos dont vous ne voulez pas.
3. Choisissez une qualité et un dossier de sortie.
4. Cliquez sur **Télécharger la sélection** et suivez la progression.

Clavier : `Entrée` dans le champ URL lance l'analyse ; `Espace` coche/décoche la ligne sélectionnée.

### Ligne de commande

```bash
python yt_playlist.py
```

Collez une URL, appuyez sur Entrée : le script télécharge toute la playlist puis en
redemande une autre. Tapez `q`, `quit`, `exit` ou envoyez une ligne vide pour quitter.
Les réglages sont en haut de `yt_playlist.py` (`QUALITY`, `OUTPUT_DIR`, `COOKIES_FILE`,
`COOKIES_FROM_BROWSER`, `FORCE_AAC`).

## Référence des options (interface graphique)

| Option | Rôle |
| --- | --- |
| Qualité | Hauteur vidéo maximale, ou extraction audio seule (MP3 / M4A). |
| Dossier | Dossier de sortie racine. Par défaut `~/Downloads/yt_playlist`. |
| Audio AAC | Ré-encode l'audio en AAC 192 kbps pendant la fusion, pour les lecteurs qui ne lisent pas l'Opus (fichiers muets). Ne concerne que les téléchargements vidéo. |
| Fichier cookies | Chemin d'un `cookies.txt` exporté avec une extension navigateur comme « Get cookies.txt locally ». |
| Cookies navigateur | Lit les cookies directement depuis Edge, Chrome, Firefox, Brave, Opera ou Safari. Le navigateur doit être entièrement fermé. |

Laissez les deux options de cookies vides pour commencer : elles sont rarement utiles une
fois Deno installé. Utilisez-les pour les vidéos soumises à une limite d'âge ou privées.

## Dépannage

| Symptôme | Cause probable et solution |
| --- | --- |
| `HTTP Error 403: Forbidden` | Deno absent ou hors du `PATH` (pastille **Deno** rouge). Installez-le et relancez l'application. |
| Téléchargements limités à 720p | ffmpeg introuvable (pastille **ffmpeg** rouge). Lancez `pip install -U imageio-ffmpeg`. |
| La vidéo n'a pas de son | Audio Opus. Cochez **Audio AAC** (ou `FORCE_AAC = True` en ligne de commande). |
| `Sign in to confirm your age` | Fournissez des cookies (fichier ou navigateur). |
| L'analyse échoue ou ne trouve aucune vidéo | Vérifiez que l'URL est une playlist/vidéo publique ou non répertoriée ; l'onglet **Journal** donne la raison. |
| Certaines vidéos affichent *Erreur* | Elles ont échoué et ont été ignorées volontairement. Le **Journal** explique pourquoi ; relancez pour ne retenter que celles-là. |
| Erreurs d'extraction après un changement de YouTube | Mettez à jour yt-dlp : `pip install -U --pre "yt-dlp[default]"`. |
| `No module named '_tkinter'` | Installez Tkinter : `sudo apt install python3-tk` (Debian/Ubuntu). |

## Organisation du projet

```
yt_playlist_gui.py   Interface graphique (Tkinter)
yt_playlist.py       Version en ligne de commande
requirements.txt     Dépendances Python
README.md            Documentation (anglais)
README.fr.md         Ce fichier (français)
```

## Mentions légales

Cet outil est destiné au téléchargement de contenus dont vous êtes l'auteur, publiés sous
licence permissive, ou que vous avez l'autorisation de télécharger. Télécharger du contenu
protégé sans autorisation peut enfreindre les conditions d'utilisation de YouTube et le
droit d'auteur de votre pays. Vous êtes responsable de l'usage que vous en faites.

## Licence

Choisissez une licence pour votre dépôt (MIT est un choix courant) et indiquez-la ici,
avec un fichier `LICENSE`.
