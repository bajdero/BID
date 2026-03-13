"""
bid/image_processing.py
Operacje na obrazach: skalowanie, zmiana alpha, konwersja przestrzeni barwowej,
nakładanie watermarku, czyszczenie EXIF.
"""
from __future__ import annotations

import io
import logging
import re
import warnings
from functools import lru_cache
from typing import Literal, Any

from PIL import Image, ImageCms, ExifTags

logger = logging.getLogger("BID")


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
    icc = img.info.get("icc_profile", "")
    if icc:
        logger.debug("Konwertuję zdjęcie na sRGB (znaleziono profil ICC)")
    else:
        logger.debug("Brak profilu ICC — pomijam konwersję sRGB")
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
    logger.debug(f"Skaluję zdjęcie {img.width}x{img.height} → {longer_side}px (metoda: {method})")

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
    placement: str = "bottom-right",
) -> Image.Image:
    """Ładuje logo, skaluje je, ustawia przezroczystość i nakłada na obraz.

    Args:
        base:      Obraz bazowy (RGB lub RGBA).
        logo_path: Ścieżka do pliku logo (PNG z kanałem alpha).
        size:      Docelowy rozmiar dłuższego boku logo w px.
        opacity:   Przezroczystość logo (0–100).
        x_offset:  Odległość logo od krawędzi poziomej (px).
        y_offset:  Odległość logo od krawędzi pionowej (px).
        placement: Narożnik: "top-left", "top-right", "bottom-left", "bottom-right".

    Returns:
        Obraz RGB z nałożonym watermarkiem.
    """
    logger.debug(f"Nakładam watermark z {logo_path} (rozmiar={size}, opacity={opacity}, placement={placement})")

    full_logo = get_logo(logo_path)
    logo = image_resize(full_logo, size, resamle=Image.NEAREST)
    logo = image_change_alpha(logo, opacity)

    # Oblicz pozycję w zależności od narożnika
    if placement == "top-left":
        pos_x = x_offset
        pos_y = y_offset
    elif placement == "top-right":
        pos_x = base.width - x_offset - logo.width
        pos_y = y_offset
    elif placement == "bottom-left":
        pos_x = x_offset
        pos_y = base.height - y_offset - logo.height
    else:  # "bottom-right" (domyślny)
        pos_x = base.width - x_offset - logo.width
        pos_y = base.height - y_offset - logo.height

    # Tworzymy przezroczystą warstwę o rozmiarze bazowego obrazu
    logo_layer = Image.new("RGBA", base.size)
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
    logger.info(f"[PROCESS] Start: {folder_name}/{photo_name}")
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
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="PIL.TiffImagePlugin")
                raw_photo = Image.open(photo_path)
                raw_photo.load()  # force-load data while warnings are suppressed
        except Exception as exc:
            results["success"] = False
            results["error_msg"] = f"Błąd otwarcia pliku '{photo_path}': {exc}"
            logger.error(f"[PROCESS] Błąd otwarcia: {folder_name}/{photo_name} — {exc}")
            return results

        # ---- EXIF ----
        try:
            exif = exif_clean_from_tiff(raw_photo.getexif())
        except Exception as exc:
            results["success"] = False
            results["error_msg"] = f"Błąd odczytu EXIF '{photo_path}': {exc}"
            logger.error(f"[PROCESS] Błąd EXIF: {folder_name}/{photo_name} — {exc}")
            return results

        # Standardowe pola EXIF
        exif[0x0001] = "R98"
        exif[0x00FE] = 0x1
        exif[0x0106] = 2
        exif[0x0112] = 0

        # Artist (0x013B): zachowaj oryginalnego autora z EXIF; jeśli brak — użyj folder_name
        _raw_artist = raw_photo.getexif().get(0x013B)
        if isinstance(_raw_artist, bytes):
            _raw_artist = _raw_artist.decode("utf-8", errors="ignore").strip("\x00 ")
        if _raw_artist and str(_raw_artist).strip():
            exif[0x013B] = _raw_artist if isinstance(_raw_artist, bytes) else _raw_artist.encode("utf-8")
        else:
            logger.warning(f"[PROCESS] Brak autora w EXIF — użyto nazwy folderu: {folder_name}")
            exif[0x013B] = folder_name.encode("utf-8")

        exif[0xC71B] = now.strftime("%Y:%m:%d %H:%M:%S")

        orientation = "landscape" if raw_photo.width >= raw_photo.height else "portrait"

        # ---- Eksport dla każdego delivery ----
        for deliver, d_cfg in export_settings.items():
            logger.debug(f"[PROCESS] Eksport profil '{deliver}': {folder_name}/{photo_name}")
            # Optymalizacja: jeśli plik już istnieje, pomijamy ten wariant
            existing_path = existing_exports.get(deliver)
            if existing_path and os.path.isfile(existing_path):
                results["exported"][deliver] = existing_path
                logger.debug(f"[PROCESS] Pomijam istniejący eksport '{deliver}': {existing_path}")
                continue

            # Check ratio
            ratios = d_cfg.get("ratio")
            if ratios is not None:
                actual = round(raw_photo.width / raw_photo.height, 2)
                if not any(abs(actual - r) < 0.01 for r in ratios):
                    logger.debug(f"[PROCESS] Pomijam '{deliver}' — ratio {actual} poza zakresem {ratios}")
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
                logger.error(f"[PROCESS] Błąd skalowania: {folder_name}/{photo_name} profil={deliver} — {exc}")
                return results

            exif[256] = resized.width
            exif[257] = resized.height

            # Konwersja przestrzeni barwowej
            try:
                img_conv = image_convert_to_srgb(resized)
            except Exception as exc:
                results["success"] = False
                results["error_msg"] = f"Błąd konwersji sRGB w {deliver}: {exc}"
                logger.error(f"[PROCESS] Błąd sRGB: {folder_name}/{photo_name} profil={deliver} — {exc}")
                return results

            # Watermark / logo
            # Zakładamy że logo.png jest w folderze nadrzędnym względem zdjęcia?
            # Nie, w BID logo.png jest w folderze sesji.
            # folder_name to nazwa folderu sesji.
            # photo_path to pełna ścieżka.
            logo_path = os.path.join(os.path.dirname(photo_path), "logo.png")
            logo_cfg = d_cfg["logo"][orientation]
            logo_required = d_cfg.get("logo_required", False)
            if not os.path.isfile(logo_path):
                logger.warning(f"[PROCESS] BRAK LOGO: {os.path.dirname(photo_path)} — eksport bez watermarku")
                if logo_required:
                    logger.warning(f"[PROCESS] Logo wymagane w profilu '{deliver}' — pomijam folder {os.path.dirname(photo_path)}")
                    continue
                final_img = img_conv
            else:
                try:
                    final_img = apply_watermark(
                        base=img_conv,
                        logo_path=logo_path,
                        size=logo_cfg["size"],
                        opacity=logo_cfg["opacity"],
                        x_offset=logo_cfg["x_offset"],
                        y_offset=logo_cfg["y_offset"],
                        placement=logo_cfg.get("placement", "bottom-right"),
                    )
                except Exception as exc:
                    results["success"] = False
                    results["error_msg"] = f"Błąd nakładania logo w {deliver}: {exc}"
                    logger.error(f"[PROCESS] Błąd watermark: {folder_name}/{photo_name} profil={deliver} — {exc}")
                    return results

            # Nazwa pliku eksportu
            created_tag = created_date.replace(" ", "_").replace(":", "-")
            orig_stem = os.path.splitext(photo_name)[0]
            folder_tag = re.sub(r'[<>:"/\\|?*]', '_', folder_name.replace(" ", "_"))
            safe_stem = re.sub(r'[<>:"/\\|?*]', '_', orig_stem)
            export_name = f"YAPA{created_tag}_{folder_tag}_{safe_stem}"

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
                    png_meta.add_text("DocumentName", "BID")
                    png_meta.add_text("ImageDescription", "BID")
                    png_meta.add_text("DateTimeOriginal", created_date)
                    png_meta.add_text("PreviewDateTime", now.strftime("%Y:%m:%d %H:%M:%S"))
                    save_args = {"format": "PNG", "optimize": True, "compress_level": d_cfg["quality"], "pnginfo": png_meta}
                else:
                    raise ValueError(f"Nieznany format eksportu: {fmt!r}")

                export_path = os.path.join(export_folder, deliver, export_name + ext)
                os.makedirs(os.path.join(export_folder, deliver), exist_ok=True)
                final_img.save(export_path, **save_args, exif=exif.tobytes() if fmt == "JPEG" else None)
                results["exported"][deliver] = export_path
                logger.info(f"[PROCESS] Eksport '{deliver}' zapisany: {export_path}")

            except Exception as exc:
                results["success"] = False
                results["error_msg"] = f"Błąd zapisu w {deliver}: {exc}"
                return results

        results["duration"] = round(time.perf_counter() - start_time, 4)
        exported_count = len(results["exported"])
        logger.info(f"[PROCESS] Zakończono: {folder_name}/{photo_name} — "
                    f"{exported_count} eksportów w {results['duration']:.2f}s")
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


def get_all_exif(img: Image.Image) -> dict[str, str]:
    """Wyciąga wszystkie możliwe tagi EXIF w formie czytelnych dla człowieka stringów.

    Args:
        img: Obraz PIL.

    Returns:
        Słownik {tag_name: value_string}.
    """
    from PIL.TiffImagePlugin import IFDRational

    def format_value(val: Any) -> str | None:
        """Konwertuje wartość EXIF na czytelny string lub None jeśli nieczytelne."""
        if val is None:
            return ""
        if isinstance(val, (int, float, str)):
            return str(val).strip("\ufeff \t\n\r")
        if isinstance(val, IFDRational):
            if val.denominator == 0:
                return "0"
            # Specjalna obsługa dla czasu naświetlania (ułamki)
            if val.numerator < val.denominator and val.numerator != 0:
                return f"{val.numerator}/{val.denominator}"
            # Jeśli to liczba całkowita (np. 300/1), zwróć jako int
            if val.numerator % val.denominator == 0:
                return str(int(val.numerator / val.denominator))
            # W przeciwnym razie float z rozsądną precyzją
            return str(round(float(val), 4))
        if isinstance(val, bytes):
            try:
                # Próba dekodowania jako UTF-8/ASCII
                decoded = val.decode("utf-8", "ignore").strip("\ufeff\x00 \t\n\r")
                # Jeśli po dekodowaniu mamy śmieci (znaki nieczytelne), uznaj za nieczytelne
                if all(c.isprintable() or c.isspace() for c in decoded):
                    return decoded
                return None  # Nieczytelne binaria
            except:
                return None
        if isinstance(val, tuple):
            return ", ".join(str(format_value(v)) for v in val if format_value(v) is not None)
            
        # Obsługa specyficznych typów (np. daty/czasu z MakerNote)
        return str(val).strip("\x00 ")

    metadata = {}
    # Tagi, których nigdy nie chcemy zapisywać (duże binaria, offsety)
    BLACK_LIST_TAGS = {
        34665,  # ExifOffset
        34853,  # GPSInfo
        40965,  # InteropOffset
    }
    
    # Mapowanie nazw tagów PIL na bardziej standardowe (z ExifTool)
    TAG_NAME_OVERRIDE = {
        "ISOSpeedRatings": "ISO",
        "BodySerialNumber": "SerialNumber",
        "CameraOwnerName": "OwnerName",
        "DateTimeOriginal": "CreateDate",
        "DateTime": "ModifyDate",
        "ExposureBiasValue": "ExposureCompensation",
    }

    try:
        exif_data = img.getexif()
        if exif_data:
            # 1. Root tags (IFD0)
            for tag_id, value in exif_data.items():
                if tag_id in BLACK_LIST_TAGS:
                    continue
                name = ExifTags.TAGS.get(tag_id, str(tag_id))
                name = TAG_NAME_OVERRIDE.get(name, name)
                
                # Specjalna obsługa MakerNote (tag 37500)
                if tag_id == 37500:
                    # Próbujemy wyłuskać czytelne fragmenty z MakerNote
                    fmt_val = format_value(value)
                    if fmt_val: metadata["MakerNote"] = fmt_val
                    continue

                fmt_val = format_value(value)
                if fmt_val is not None:
                    if name == "FocalLength":
                        fmt_val = f"{fmt_val} mm"
                    elif name == "ExposureCompensation" or name == "ExposureBiasValue":
                        fmt_val = f"{fmt_val} EV"
                    metadata[name] = fmt_val

            # 2. Sub-IFDs
            for ifd_id in [ExifTags.IFD.Exif, ExifTags.IFD.GPSInfo, ExifTags.IFD.Interop]:
                try:
                    ifd = exif_data.get_ifd(ifd_id)
                    if not ifd:
                        continue
                    for tag_id, value in ifd.items():
                        if tag_id in BLACK_LIST_TAGS:
                            continue
                        if ifd_id == ExifTags.IFD.GPSInfo:
                            name = ExifTags.GPSTAGS.get(tag_id, str(tag_id))
                        else:
                            name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        
                        name = TAG_NAME_OVERRIDE.get(name, name)
                        fmt_val = format_value(value)
                        if fmt_val is not None:
                            if name == "FocalLength":
                                fmt_val = f"{fmt_val} mm"
                            elif name == "ExposureCompensation":
                                fmt_val = f"{fmt_val} EV"
                            metadata[name] = fmt_val
                except Exception as e:
                    logger.debug(f"Pominięto IFD {ifd_id}: {e}")
                
    except Exception as exc:
        logger.warning(f"Błąd ekstrakcji EXIF: {exc}")

    # 3. IPTC Info
    try:
        from PIL import IptcImagePlugin
        iptc = IptcImagePlugin.getiptcinfo(img)
        if iptc:
            # Common IPTC mapping (Dataset, Record) -> Name
            # Based on IPTC / IIM standard
            IPTC_NAMES = {
                (2, 5): "ObjectName",
                (2, 25): "Keywords",
                (2, 40): "SpecialInstructions",
                (2, 55): "DateCreated",
                (2, 60): "TimeCreated",
                (2, 62): "DigitalCreationDate",
                (2, 63): "DigitalCreationTime",
                (2, 80): "By-line",
                (2, 85): "By-lineTitle",
                (2, 90): "City",
                (2, 92): "Sub-location",
                (2, 95): "Province-State",
                (2, 101): "Country",
                (2, 103): "OriginalTransmissionReference",
                (2, 105): "Headline",
                (2, 110): "Credit",
                (2, 115): "Source",
                (2, 116): "CopyrightNotice",
                (2, 120): "Caption-Abstract",
                (2, 122): "Writer-Editor",
            }
            for tag, val in iptc.items():
                name = IPTC_NAMES.get(tag, f"IPTC:{tag}")
                fmt_val = format_value(val)
                if fmt_val:
                    metadata[name] = fmt_val
    except Exception as exc:
        logger.debug(f"Błąd ekstrakcji IPTC: {exc}")

    # 4. XMP Info
    try:
        xmp_raw = img.info.get("xmp")
        if xmp_raw:
            if isinstance(xmp_raw, bytes):
                xmp_str = xmp_raw.decode("utf-8", "ignore")
            else:
                xmp_str = str(xmp_raw)
            
            import re
            found_xmp = {}
            # Match <prefix:tag>value</prefix:tag> or prefix:tag="value"
            tags = re.findall(r'<([\w:]+)[^>]*>([^<]+)</\1>', xmp_str)
            for tag, val in tags:
                clean_tag = tag.split(":")[-1]
                if clean_tag not in metadata and len(val) < 200:
                    found_xmp[f"XMP:{clean_tag}"] = val.strip()
            
            attrs = re.findall(r'([\w:]+)="([^"]+)"', xmp_str)
            for tag, val in attrs:
                clean_tag = tag.split(":")[-1]
                if clean_tag not in metadata and len(val) < 200:
                    found_xmp[f"XMP:{clean_tag}"] = val.strip()
            
            metadata.update(found_xmp)
    except Exception as exc:
        logger.debug(f"Błąd ekstrakcji XMP: {exc}")

    # 5. ICC Profile Info
    try:
        icc = img.info.get("icc_profile")
        if icc:
            from PIL import ImageCms
            import io
            profile = ImageCms.getProfileDescription(io.BytesIO(icc))
            if profile:
                metadata["ICC:ProfileDescription"] = profile.strip()
            manufacturer = ImageCms.getProfileManufacturer(io.BytesIO(icc))
            if manufacturer:
                metadata["ICC:Manufacturer"] = manufacturer.strip()
            model = ImageCms.getProfileModel(io.BytesIO(icc))
            if model:
                metadata["ICC:Model"] = model.strip()
    except Exception as exc:
        logger.debug(f"Błąd ekstrakcji ICC: {exc}")

    # 6. Always use PIL's actual image dimensions — reliable, rotation-corrected,
    # and independent of potentially inaccurate or absent EXIF dimension tags.
    # PIL's .width/.height always reflects the true decoded image dimensions.
    metadata["ImageWidth"] = str(img.width)
    metadata["ImageLength"] = str(img.height)

    logger.debug(f"[EXIF] Odczytano {len(metadata)} tagów z obrazu")
    return metadata


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
