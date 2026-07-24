"""Capture, resize, crop, upload — pipeline d'image parametre.

Usage:
    from ArtizBoardCommon.capture import capture_and_upload, FORMATS
    url, name = capture_and_upload(file_bytes, "carte_produit", supabase_url, service_key)
"""
import io, uuid
from PIL import Image, ImageOps
from supabase import create_client

QUALITY = 85
BUCKET = "images"

class CaptureError(Exception):
    pass

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
    w, h = FORMATS[format_key]
    uid = uuid.uuid4().hex[:8]
    return f"{format_key}_{uid}_{w}x{h}.webp"

def process_image(data: bytes, format_key: str) -> io.BytesIO:
    if format_key not in FORMATS:
        raise CaptureError(f"Format inconnu: {format_key}. Formats: {list(FORMATS.keys())}")

    target_w, target_h = FORMATS[format_key]
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    img_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if img_ratio > target_ratio:
        new_h = target_h
        new_w = int(target_h * img_ratio)
    else:
        new_w = target_w
        new_h = int(target_w / img_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    output = io.BytesIO()
    img.save(output, format="WEBP", quality=QUALITY)
    output.seek(0)
    return output

def upload(supabase_url: str, service_key: str, image_data: io.BytesIO, format_key: str) -> str:
    sb = create_client(supabase_url, service_key)
    filename = _build_name(format_key)
    path = f"{format_key}/{filename}"

    sb.storage.from_(BUCKET).upload(
        path=path,
        file=image_data.getvalue(),
        file_options={"content-type": "image/webp"}
    )
    return f"{supabase_url}/storage/v1/object/public/{BUCKET}/{path}"

def capture_and_upload(file_bytes: bytes, format_key: str, supabase_url: str, service_key: str) -> tuple[str, str]:
    processed = process_image(file_bytes, format_key)
    url = upload(supabase_url, service_key, processed, format_key)
    return url, _build_name(format_key)
