"""
bid/image_processing.py
Operacje na obrazach: skalowanie, zmiana alpha, konwersja przestrzeni barwowej,
nakładanie watermarku, czyszczenie EXIF.
"""
from __future__ import annotations

import io
import logging
from functools import lru_cache
from typing import Literal, Any

from PIL import Image, ImageCms, ExifTags

logger = logging.getLogger("Yapa_CM")


@lru_cache(maxsize=32)
def get_logo(logo_path: str) -> Image.Image:
    """Wczytuje i cache'uje logo."""
    logger.debug(f"Wczytuję logo (cache miss): {logo_path}")
    return Image.open(logo_path).convert("RGBA")


# ---------------------------------------------------------------------------
# Konwersja przestrzeni barwowej
# ---------------------------------------------------------------------------

def image_convert_to_srgb(img: Image.Image) -> Image.Image:
    """Konwertuje obraz do przestrzeni barwowej sRGB (jeśli posiada profil ICC).

    Args:
        img: Obraz w dowolnej przestrzeni barwowej.

    Returns:
        Obraz w przestrzeni sRGB.
    """
    logger.debug("Konwertuję zdjęcie na sRGB")
    icc = img.info.get("icc_profile", "")
    if icc:
        io_handle = io.BytesIO(icc)
        src_profile = ImageCms.ImageCmsProfile(io_handle)
        dst_profile = ImageCms.createProfile("sRGB")
        img = ImageCms.profileToProfile(img, src_profile, dst_profile)
    return img


# ---------------------------------------------------------------------------
# Skalowanie
# ---------------------------------------------------------------------------

def image_resize(
    img: Image.Image,
    longer_side: int = 1600,
    resamle: Image.Resampling = Image.LANCZOS,
    method: Literal["longer", "width", "height"] = "longer",
    reducing_gap: float | None = None,
) -> Image.Image:
    """Skaluje obraz zachowując proporcje.

    Args:
        img:          Obraz wejściowy.
        longer_side:  Docelowa długość wybranej krawędzi w pikselach.
        resamle:      Metoda resamplingu (domyślnie LANCZOS).
        method:       Która krawędź wyznacza skalowanie:
                      ``"longer"`` — dłuższy bok,
                      ``"width"``  — szerokość,
                      ``"height"`` — wysokość.
        reducing_gap: Parametr PIL optymalizujący wielokrotne pomniejszania.

    Returns:
        Przeskalowany obraz.
    """
    logger.debug(f"Skaluję zdjęcie do {longer_side} px (metoda: {method})")

    if method == "longer":
        ratio = longer_side / max(img.size)
    elif method == "width":
        ratio = longer_side / img.width
    elif method == "height":
        ratio = longer_side / img.height
    else:
        raise ValueError(f"Unknown resize method: {method!r}")

    new_w = int(img.width * ratio)
    new_h = int(img.height * ratio)
    return img.resize((new_w, new_h), resample=resamle, reducing_gap=reducing_gap)


# ---------------------------------------------------------------------------
# Kanał alpha
# ---------------------------------------------------------------------------

def image_change_alpha(img: Image.Image, alpha: int | float) -> Image.Image:
    """Skaluje kanał alpha obrazu.

    Args:
        img:   Obraz z kanałem alpha (tryb RGBA).
        alpha: Przezroczystość w procentach (0–100).

    Returns:
        Obraz ze zmodyfikowanym kanałem alpha.
    """
    factor = alpha / 100.0
    old_alpha = img.getchannel("A")
    new_alpha = old_alpha.point(lambda i: int(i * factor))
    img.putalpha(new_alpha)
    return img


# ---------------------------------------------------------------------------
# Nakładanie watermarku (logo)
# ---------------------------------------------------------------------------

def apply_watermark(
    base: Image.Image,
    logo_path: str,
    size: int,
    opacity: int,
    x_offset: int,
    y_offset: int,
) -> Image.Image:
    """Ładuje logo, skaluje je, ustawia przezroczystość i nakłada na obraz.

    Args:
        base:     Obraz bazowy (RGB lub RGBA).
        logo_path: Ścieżka do pliku logo (PNG z kanałem alpha).
        size:     Docelowy rozmiar dłuższego boku logo w px.
        opacity:  Przezroczystość logo (0–100).
        x_offset: Odległość prawej krawędzi logo od prawej krawędzi obrazu (px).
        y_offset: Odległość dolnej krawędzi logo od dolnej krawędzi obrazu (px).

    Returns:
        Obraz RGB z nałożonym watermarkiem.
    """
    logger.debug(f"Nakładam watermark z {logo_path}")

    full_logo = get_logo(logo_path)
    logo = image_resize(full_logo, size, resamle=Image.NEAREST)
    logo = image_change_alpha(logo, opacity)

    # Tworzymy przezroczystą warstwę o rozmiarze bazowego obrazu
    logo_layer = Image.new("RGBA", base.size)
    pos_x = base.width - x_offset - logo.width
    pos_y = base.height - y_offset - logo.height
    logo_layer.paste(logo, (pos_x, pos_y))

    # Kompozytujemy
    base_rgba = base.convert("RGBA")
    base_rgba.putalpha(255)
    result = Image.new("RGBA", base.size)
    result = Image.alpha_composite(result, base_rgba)
    result = Image.alpha_composite(result, logo_layer)
    return result.convert("RGB")


# ---------------------------------------------------------------------------
# Worker Task for Parallel Processing
# ---------------------------------------------------------------------------

def process_photo_task(
    photo_path: str,
    folder_name: str,
    photo_name: str,
    created_date: str,
    export_folder: str,
    export_settings: dict,
    existing_exports: dict,
) -> dict:
    """Przetwarza jedno zdjęcie (wszystkie warianty) w osobnym procesie.

    Returns:
        Słownik z wynikami: {success, exported, duration, error_msg}.
    """
    import os
    import time
    import datetime
    from PIL import Image

    start_time = time.perf_counter()
    now = datetime.datetime.now()
    # Explicit types to satisfy strict linters if needed
    results: dict[str, Any] = {
        "success": True, 
        "exported": {}, 
        "duration": 0.0, 
        "error_msg": None
    }

    try:
        # ---- Wczytywanie ----
        try:
            raw_photo = Image.open(photo_path)
        except Exception as exc:
            results["success"] = False
            results["error_msg"] = f"Błąd otwarcia pliku '{photo_path}': {exc}"
            return results

        # ---- EXIF ----
        try:
            exif = exif_clean_from_tiff(raw_photo.getexif())
        except Exception as exc:
            results["success"] = False
            results["error_msg"] = f"Błąd odczytu EXIF '{photo_path}': {exc}"
            return results

        # Standardowe pola EXIF
        exif[0x0001] = "R98"
        exif[0x00FE] = 0x1
        exif[0x0106] = 2
        exif[0x0112] = 0
        exif[0x013B] = folder_name.encode("utf-8")
        exif[0xC71B] = now.strftime("%Y:%m:%d %H:%M:%S")

        orientation = "landscape" if raw_photo.width >= raw_photo.height else "portrait"

        # ---- Eksport dla każdego delivery ----
        for deliver, d_cfg in export_settings.items():
            # Optymalizacja: jeśli plik już istnieje, pomijamy ten wariant
            existing_path = existing_exports.get(deliver)
            if existing_path and os.path.isfile(existing_path):
                results["exported"][deliver] = existing_path
                continue

            # Check ratio
            ratios = d_cfg.get("ratio")
            if ratios is not None:
                actual = round(raw_photo.width / raw_photo.height, 2)
                if actual not in ratios:
                    continue

            # Skalowanie
            try:
                resized = image_resize(
                    raw_photo,
                    d_cfg["size"],
                    method=d_cfg.get("size_type", "longer"),
                )
            except Exception as exc:
                results["success"] = False
                results["error_msg"] = f"Błąd skalowania w {deliver}: {exc}"
                return results

            exif[256] = resized.width
            exif[257] = resized.height

            # Konwersja przestrzeni barwowej
            try:
                img_conv = image_convert_to_srgb(resized)
            except Exception as exc:
                results["success"] = False
                results["error_msg"] = f"Błąd konwersji sRGB w {deliver}: {exc}"
                return results

            # Watermark / logo
            # Zakładamy że logo.png jest w folderze nadrzędnym względem zdjęcia?
            # Nie, w BID logo.png jest w folderze sesji.
            # folder_name to nazwa folderu sesji.
            # photo_path to pełna ścieżka.
            logo_path = os.path.join(os.path.dirname(photo_path), "logo.png")
            logo_cfg = d_cfg["logo"][orientation]
            try:
                final_img = apply_watermark(
                    base=img_conv,
                    logo_path=logo_path,
                    size=logo_cfg["size"],
                    opacity=logo_cfg["opacity"],
                    x_offset=logo_cfg["x_offset"],
                    y_offset=logo_cfg["y_offset"],
                )
            except Exception as exc:
                results["success"] = False
                results["error_msg"] = f"Błąd nakładania logo w {deliver}: {exc}"
                return results

            # Nazwa pliku eksportu
            created_tag = created_date.replace(" ", "_").replace(":", "-")
            orig_stem = os.path.splitext(photo_name)[0]
            folder_tag = folder_name.replace(" ", "_")
            export_name = f"YAPA{created_tag}_{folder_tag}_{orig_stem}"

            # Zapis
            fmt = d_cfg["format"]
            try:
                if fmt == "JPEG":
                    ext = ".jpg"
                    save_args = {"format": "JPEG", "optimize": True, "quality": d_cfg["quality"]}
                elif fmt == "PNG":
                    ext = ".png"
                    from PIL.PngImagePlugin import PngInfo
                    png_meta = PngInfo()
                    png_meta.add_text("Artist", folder_name)
                    png_meta.add_text("OriginalRawFileName", photo_name)
                    png_meta.add_text("DocumentName", "YAPA")
                    png_meta.add_text("ImageDescription", "YAPA")
                    png_meta.add_text("DateTimeOriginal", created_date)
                    png_meta.add_text("PreviewDateTime", now.strftime("%Y:%m:%d %H:%M:%S"))
                    save_args = {"format": "PNG", "optimize": True, "compress_level": d_cfg["quality"], "pnginfo": png_meta}
                else:
                    raise ValueError(f"Nieznany format eksportu: {fmt!r}")

                export_path = os.path.join(export_folder, deliver, export_name + ext)
                final_img.save(export_path, **save_args, exif=exif.tobytes() if fmt == "JPEG" else None)
                results["exported"][deliver] = export_path

            except Exception as exc:
                results["success"] = False
                results["error_msg"] = f"Błąd zapisu w {deliver}: {exc}"
                return results

        results["duration"] = round(time.perf_counter() - start_time, 4)
        return results

    except Exception as exc:
        results["success"] = False
        results["error_msg"] = f"Nieoczekiwany błąd: {exc}"
        return results


# ---------------------------------------------------------------------------
# Czyszczenie EXIF
# ---------------------------------------------------------------------------

def exif_clean_from_tiff(exif: Image.Exif) -> Image.Exif:
    """Usuwa tagi EXIF specyficzne dla formatu TIFF, które są nieprawidłowe w JPEG/PNG.

    Args:
        exif: Obiekt EXIF obrazu.

    Returns:
        Oczyszczony obiekt EXIF.
    """
    logger.debug("Czyszczę EXIF z tagów TIFF")
    tags_to_remove = [
        273,  # StripOffsets
        279,  # StripByteCounts
        269,  # DocumentName
        317,  # Predictor
        259,  # Compression
        258,  # BitsPerSample
        262,  # PhotometricInterpretation
        277,  # SamplesPerPixel
        278,  # RowsPerStrip
        339,  # SampleFormat
        284,  # PlanarConfiguration
    ]
    for key in tags_to_remove:
        exif.pop(key, None)
    return exif


# ---------------------------------------------------------------------------
# Pomocnicze (debug)
# ---------------------------------------------------------------------------

def print_exif_ifd0(exif: Image.Exif) -> None:
    """Wyświetla tagi EXIF z głównego bloku IFD0 (do celów diagnostycznych).

    Args:
        exif: Obiekt EXIF obrazu.
    """
    for key, val in exif.items():
        if key in ExifTags.TAGS and ExifTags.TAGS[key]:
            print(f"{key}|{ExifTags.TAGS[key]}: {val}")


def print_exif_all(exif: Image.Exif) -> None:
    """Wyświetla kompletny EXIF łącznie z zagnieżdżonymi blokami IFD (do celów diagnostycznych).

    Args:
        exif: Obiekt EXIF obrazu.
    """
    ifd_lookup = {i.value: i.name for i in ExifTags.IFD}
    for tag_code, value in exif.items():
        if tag_code in ifd_lookup:
            print(f"IFD '{ifd_lookup[tag_code]}' (code {tag_code}):")
            for nested_key, nested_value in exif.get_ifd(tag_code).items():
                name = (
                    ExifTags.GPSTAGS.get(nested_key)
                    or ExifTags.TAGS.get(nested_key)
                    or nested_key
                )
                print(f"  -{nested_key} | {name}: {nested_value}")
        else:
            print(f"{tag_code} | {ExifTags.TAGS.get(tag_code)}: {value}")
