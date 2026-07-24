# Skill: Capture & Canvas — Photo Paramétrée

## 0. Contexte

**Projet** : ArtizBoard
**Module** : `ArtizBoardCommon/capture.py` — utilitaire de capture et processing d'image
**Utilisateurs** : Admin (produits, logo), Staff (QR, vérification), Site web (affichage)
**Dépendances** : [[design-system]], `Supabase Storage`, `Pillow`, `ft.FilePicker`
**Prérequis** : Caméra disponible ou fichier image, bucket `images` dans Supabase

## 1. Fonction Principale

### Type : Système Fermé

```
ENTRÉE                               →  TRAITEMENT                              →  SORTIE
Source (caméra, fichier, scan)         Redimensionner au format cible           ├─ Image traitée (bytes)
Format cible (carte, bannière...)      Rogner si ratio différent                ├─ URL Supabase Storage
Type d'objet (produit, logo, qr)       Compression optimisée (WebP)             ├─ Nom unique (UUID)
                                       Naming rule (uuid_xxx_400x300.webp)      └─ Métadonnées (dimensions, taille)
```

- **Entrée** : Une photo brute depuis caméra ou fichier
- **Sortie** : Une URL publique prête à être stockée en base
- **Traitement** : Redimensionnement → recadrage → compression → upload → URL

## 2. Contraintes Fonctionnelles

### Tableau global

| # | Contrainte |
|---|---|
| C1 | Toute image capturée est redimensionnée à un **format cible** prédéfini |
| C2 | Le ratio est **préservé** — l'image est recadrée (centrée) si nécessaire |
| C3 | Le nom du fichier suit une règle fixe : `{type}_{uuid8}_{largeur}x{hauteur}.webp` |
| C4 | Le format de sortie est **WebP** (compression optimale pour le web) |
| C5 | La compression est configurable : `QUALITY` (défaut 85%) |
| C6 | L'upload se fait vers Supabase Storage dans le dossier `/images/{type}/` |
| C7 | L'URL publique est retournée pour stockage immédiat en base |

### Sous-système A — Formats standards

**Fonction** : Définir les dimensions pour chaque usage

| Format | Largeur | Hauteur | Ratio | Usage |
|---|---|---|---|---|
| `carte_produit` | 400 | 300 | 4:3 | Carte/catalogue WordPress + Flet |
| `detail_produit` | 800 | 600 | 4:3 | Détail produit Admin |
| `logo` | 256 | 256 | 1:1 | Logo établissement |
| `banniere` | 1200 | 400 | 3:1 | Hero bannière WordPress |
| `thumbnail` | 150 | 150 | 1:1 | Miniature, badges |
| `galerie` | 600 | 400 | 3:2 | Page galerie WordPress |
| `qr_scan` | 512 | 512 | 1:1 | Capture QR code pour décodage |
| `avatar` | 128 | 128 | 1:1 | Photo de profil utilisateur |

### Sous-système B — Règles de nommage

**Fonction** : Générer un nom unique et traçable

| # | Contrainte |
|---|---|
| B1 | Format : `{type}_{uuid8}_{w}x{h}.webp` |
| B2 | `type` = le format cible (`produit`, `logo`, `banniere`, etc.) |
| B3 | `uuid8` = 8 premiers caractères de `uuid.uuid4().hex` |
| B4 | `{w}x{h}` = dimensions finales de l'image |
| B5 | Exemple : `produit_a1b2c3d4_400x300.webp` |
| B6 | Le nom est garanti **unique** par UUID, évite les collisions |

### Sous-système C — Pipeline de traitement

**Fonction** : Transformer l'image brute en image finale

| # | Contrainte |
|---|---|
| C1 | Redimensionner l'image pour que le **plus petit côté** atteigne la dimension cible |
| C2 | Recadrer au centre pour respecter le ratio exact du format |
| C3 | Convertir en **RGB** si nécessaire (supporte PNG, JPEG, BMP, TIFF) |
| C4 | Sauvegarder en **WebP** avec `quality=QUALITY` |
| C5 | Les métadonnées EXIF sont **conservées** (date, orientation) |
| C6 | L'orientation EXIF est appliquée avant redimensionnement |

### Sous-système D — Upload + URL

**Fonction** : Stocker l'image et retourner son URL

| # | Contrainte |
|---|---|
| D1 | L'image est uploadée dans le bucket `images`, dossier `/{type}/` |
| D2 | L'URL publique est construite : `https://{project}.supabase.co/storage/v1/object/public/images/{type}/{nom}` |
| D3 | Si l'upload échoue, une exception `CaptureError` est levée |
| D4 | L'URL est immédiatement exploitable (pas de délai de cache) |

## 3. Code complet

```python
# ArtizBoardCommon/capture.py
"""Capture, resize, crop, upload — pipeline d'image paramétré."""
import io, uuid
from pathlib import Path
from PIL import Image, ImageOps
from supabase import create_client

# ── Config ──
QUALITY = 85
BUCKET = "images"

class CaptureError(Exception):
    pass

# ── Formats ──
FORMATS = {
    "carte_produit":  (400, 300),
    "detail_produit": (800, 600),
    "logo":           (256, 256),
    "banniere":       (1200, 400),
    "thumbnail":      (150, 150),
    "galerie":        (600, 400),
    "qr_scan":        (512, 512),
    "avatar":         (128, 128),
}

def _build_name(format_key: str) -> str:
    """Genere un nom unique : produit_a1b2c3d4_400x300.webp"""
    w, h = FORMATS[format_key]
    uid = uuid.uuid4().hex[:8]
    return f"{format_key}_{uid}_{w}x{h}.webp"

def process_image(data: bytes, format_key: str) -> io.BytesIO:
    """Redimensionne + recadre + convertit en WebP.
    
    Args:
        data: bytes bruts de l'image (PNG, JPEG, BMP, TIFF...)
        format_key: cle dans FORMATS ('carte_produit', 'logo', etc.)
    
    Returns:
        BytesIO contenant l'image WebP traitée
    """
    if format_key not in FORMATS:
        raise CaptureError(f"Format inconnu: {format_key}. Choisir parmi: {list(FORMATS.keys())}")
    
    target_w, target_h = FORMATS[format_key]
    img = Image.open(io.BytesIO(data))
    
    # Appliquer orientation EXIF
    img = ImageOps.exif_transpose(img)
    
    # Convertir en RGB si nécessaire
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    
    # Redimensionner : adapter au plus petit côté
    img_ratio = img.width / img.height
    target_ratio = target_w / target_h
    
    if img_ratio > target_ratio:
        # Image plus large que la cible → adapter la hauteur
        new_h = target_h
        new_w = int(target_h * img_ratio)
    else:
        # Image plus haute que la cible → adapter la largeur
        new_w = target_w
        new_h = int(target_w / img_ratio)
    
    img = img.resize((new_w, new_h), Image.LANCZOS)
    
    # Recadrer au centre
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))
    
    # Sauvegarder en WebP
    output = io.BytesIO()
    img.save(output, format="WEBP", quality=QUALITY)
    output.seek(0)
    return output

def upload(supabase_url: str, service_key: str, image_data: io.BytesIO, format_key: str) -> str:
    """Upload l'image traitée vers Supabase Storage.
    
    Returns:
        URL publique de l'image
    """
    sb = create_client(supabase_url, service_key)
    filename = _build_name(format_key)
    path = f"{format_key}/{filename}"
    
    sb.storage.from_(BUCKET).upload(
        path=path,
        file=image_data.getvalue(),
        file_options={"content-type": "image/webp"}
    )
    
    return f"{supabase_url}/storage/v1/object/public/{BUCKET}/{path}"

def capture_and_upload(
    file_bytes: bytes,
    format_key: str,
    supabase_url: str,
    service_key: str
) -> tuple[str, str]:
    """Pipeline complet : capture → traitement → upload.
    
    Args:
        file_bytes: image brute
        format_key: cle format ('carte_produit', 'logo', etc.)
        supabase_url: URL du projet Supabase
        service_key: service_role key
    
    Returns:
        (url_publique, nom_fichier)
    """
    processed = process_image(file_bytes, format_key)
    url = upload(supabase_url, service_key, processed, format_key)
    filename = _build_name(format_key)
    return url, filename
```

### Intégration Flet — Admin (existant, à enrichir)

```python
# Dans apps/admin/__main__.py
from ArtizBoardCommon.capture import capture_and_upload, FORMATS

def upload_photo(self, e):
    def on_picked(url, filename):
        photo_url.value = url
        photo_dim.value = "400×300"  # Info visuelle
        photo_url.update(); photo_dim.update()
    
    self._pending_upload = lambda f: _process(f, on_picked)
    self.file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

def _process(file_path: str, callback):
    with open(file_path, "rb") as fh:
        data = fh.read()
    url, name = capture_and_upload(data, "carte_produit", SUPABASE_URL, SUPABASE_SERVICE_KEY)
    callback(url, name)
```

## 4. Deux exemples

### Exemple 1 — Photo produit pour la carte (cas simple)

```python
# Le restaurateur prend une photo de son plat avec son téléphone
# L'image fait 3024×4032 pixels (12 MP)

with open("photo_brute.jpg", "rb") as f:
    raw = f.read()

url, name = capture_and_upload(raw, "carte_produit",
    "https://xxx.supabase.co", "sb_secret_...")

# Résultat :
# - Image redimensionnée à 400×300, recadrée centrée
# - Format WebP, compression 85%
# - Nom : carte_produit_a1b2c3d4_400x300.webp
# - URL : https://xxx.supabase.co/storage/v1/object/public/images/carte_produit/carte_produit_a1b2c3d4_400x300.webp
# - Stockée dans produits.photo_url
# - Affichée sur le site WordPress et l'app Flet en 400×300
```

### Exemple 2 — Logo + Bannière pour le site (cas complexe)

```python
# L'admin upload un logo carré mais veut aussi une bannière dérivée
logo_bytes = open("logo.png", "rb").read()

# Pipeline logo (1:1)
url_logo, _ = capture_and_upload(logo_bytes, "logo", SUPABASE_URL, SK)
# → logo_a1b2c3d4_256x256.webp → etablissements.logo_url

# Pipeline bannière (3:1) — recadrage centré automatique
url_banner, _ = capture_and_upload(logo_bytes, "banniere", SUPABASE_URL, SK)
# → banniere_e5f6g7h8_1200x400.webp → theme_config.hero_image_url

# Résultat : le même fichier source donne 2 images aux formats corrects
```

## 5. Step by Step — Implémentation

| Ordre | Action | Fichier | Résultat |
|---|---|---|---|
| 1 | Installer Pillow | `pip install Pillow` | Dépendance OK |
| 2 | Créer `capture.py` | `ArtizBoardCommon/capture.py` | Module réutilisable |
| 3 | Définir `FORMATS` | `capture.py` | 8 formats standards |
| 4 | Implémenter `process_image` | `capture.py` | Redimensionnement + crop |
| 5 | Implémenter `upload` | `capture.py` | Upload Supabase Storage |
| 6 | Implémenter `capture_and_upload` | `capture.py` | Pipeline complet |
| 7 | Intégrer dans Admin | `apps/admin/__main__.py` | Upload produit + logo |
| 8 | Tester : photo brute → URL | `python -c "..."` | URL valide |

## 6. Checklist

- [ ] `capture.py` créé dans ArtizBoardCommon
- [ ] 8 formats définis avec leurs dimensions
- [ ] Pipeline : resize → crop → convert WebP → upload
- [ ] Noms uniques via UUID
- [ ] Gestion orientation EXIF
- [ ] Intégré dans Admin (produits + logo)
- [ ] Intégré dans site WordPress (affichage)
- [ ] Tests : `tests/test_capture.py`

## Emplacement
- Module : `ArtizBoardCommon/capture.py`
- Usage Admin : `apps/admin/__main__.py` (déjà partiellement intégré)
- Usage WordPress : lecture des URLs depuis Supabase
