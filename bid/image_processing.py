"""
bid/image_processing.py
Operacje na obrazach: skalowanie, zmiana alpha, konwersja przestrzeni barwowej,
nakładanie watermarku, czyszczenie EXIF.
"""
from __future__ import annotations

import io
import logging
from typing import Literal

from PIL import Image, ImageCms, ExifTags

logger = logging.getLogger("Yapa_CM")


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

    full_logo: Image.Image = Image.open(logo_path).convert("RGBA")
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
