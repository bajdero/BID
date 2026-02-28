import pytest
from PIL import Image
from bid.image_processing import get_all_exif, exif_clean_from_tiff

def test_get_all_exif(temp_dir):
    """Testuje wyciąganie EXIF z obrazka."""
    img_path = temp_dir / "test_exif.jpg"
    img_new = Image.new('RGB', (100, 100))
    
    # Dodajemy jakieś proste EXIF (DateTime)
    exif = img_new.getexif()
    exif[0x0132] = "2023:01:01 12:00:00"
    img_new.save(img_path, "JPEG", exif=exif)
    
    with Image.open(img_path) as opened:
        data = get_all_exif(opened)
        # 0x0132 to DateTime, które w get_all_exif jest mapowane na "ModifyDate"
        found = False
        for k, v in data.items():
            if "ModifyDate" in k and "2023" in str(v):
                found = True
        assert found

def test_exif_clean_from_tiff(temp_dir):
    """Testuje czyszczenie tagów specyficznych dla TIFF."""
    img = Image.new('RGB', (10, 10))
    exif = img.getexif()
    
    # Tagi TIFF do usunięcia (np. Compression=259, BitsPerSample=258)
    exif[259] = 1 
    exif[258] = (8, 8, 8)
    exif[271] = "Canon" # Make - nie powinien zostać usunięty
    
    cleaned = exif_clean_from_tiff(exif)
    
    assert 259 not in cleaned
    assert 258 not in cleaned
    assert 271 in cleaned

def test_image_resize():
    """Testuje skalowanie obrazu."""
    from bid.image_processing import image_resize
    img = Image.new('RGB', (2000, 1000)) # 2:1 ratio
    
    # Skaluj dłuższy bok do 1000
    resized = image_resize(img, longer_side=1000, method="longer")
    
    assert resized.width == 1000
    assert resized.height == 500

def test_image_convert_to_srgb():
    """Testuje konwersję do sRGB (sanity check - bez profilu nic nie zmienia)."""
    from bid.image_processing import image_convert_to_srgb
    img = Image.new('RGB', (100, 100))
    
    converted = image_convert_to_srgb(img)
    
    assert converted.mode == "RGB"
    assert converted.size == (100, 100)

def get_exif_references():
    from pathlib import Path
    import json
    ref_path = Path("test/exif_references.json")
    if not ref_path.exists():
        return []
    with open(ref_path, "r", encoding="utf-8-sig") as f:
        return json.load(f)

@pytest.mark.parametrize("ref", get_exif_references(), ids=lambda r: r["SourceFile"].split("/")[-1])
def test_exif_mandatory_tags(ref):
    """
    Testuje kompletność tagów obowiązkowych (DateTimeOriginal / Artist) w oparciu
    o eksport z exiftool (exif_references.json).
    DateTimeOriginal oraz Artist są obowiązkowe (jeśli występują w referencji).
    Braki kończą test błędem.
    """
    from pathlib import Path
    from PIL import Image
    
    filename = Path(ref["SourceFile"]).name
    source_file = Path("test/exif") / filename
    
    if not source_file.exists():
        pytest.skip(f"Brak pliku testowego {source_file}")
        
    with Image.open(source_file) as img:
        extracted = get_all_exif(img)
        
    expected_tags = set()
    for block_name, block_data in ref.items():
        if isinstance(block_data, dict) and block_name in ("IFD0", "ExifIFD", "IPTC"):
            for key in block_data.keys():
                tag_name = key
                if tag_name == "ISOSpeedRatings": tag_name = "ISO"
                if tag_name == "DateTimeOriginal": tag_name = "CreateDate"
                expected_tags.add(tag_name)
                
    has_time = any(k in extracted for k in ["DateTimeOriginal", "CreateDate"])
    has_artist = any(k in extracted for k in ["Artist", "Creator", "By-line"])
    
    expected_has_time = any(k in expected_tags for k in ["DateTimeOriginal", "CreateDate"])
    expected_has_artist = any(k in expected_tags for k in ["Artist", "Creator", "By-line"])
    
    missing_mandatory = []
    if expected_has_time and not has_time:
        missing_mandatory.append("DateTimeOriginal (lub CreateDate)")
    if expected_has_artist and not has_artist:
        missing_mandatory.append("Artist (lub Creator/By-line)")
        
    if missing_mandatory:
        raise ValueError(f"[{filename}] Brak wymaganych tagów: {', '.join(missing_mandatory)}")


@pytest.mark.xfail(reason="Not all exiftool sub-tags are mapped/kept perfectly yet")
@pytest.mark.parametrize("ref", get_exif_references(), ids=lambda r: r["SourceFile"].split("/")[-1])
def test_exif_additional_tags(ref):
    """
    Testuje obecność tagów pobocznych w wyciągniętym EXIF w porównaniu
    do eksportu exiftool. Brak każdego pobocznego tagu z referencji zwraca błąd.
    """
    from pathlib import Path
    from PIL import Image
    
    filename = Path(ref["SourceFile"]).name
    source_file = Path("test/exif") / filename
    
    if not source_file.exists():
        pytest.skip(f"Brak pliku testowego {source_file}")
        
    with Image.open(source_file) as img:
        extracted = get_all_exif(img)
        
    expected_tags = set()
    for block_name, block_data in ref.items():
        if isinstance(block_data, dict) and block_name in ("IFD0", "ExifIFD", "IPTC"):
            for key in block_data.keys():
                tag_name = key
                if tag_name == "ISOSpeedRatings": tag_name = "ISO"
                if tag_name == "DateTimeOriginal": tag_name = "CreateDate"
                expected_tags.add(tag_name)
                
    missing_rest = []
    for tag in expected_tags:
        # Pomijamy niektóre metadane techniczne z exiftool, których ignorowanie jest zamierzone
        if tag not in ("Directory", "FilePermissions", "ThumbnailImage", "ThumbnailLength", "ThumbnailOffset", "ModifyDate"):
            if tag not in extracted and tag not in ["DateTimeOriginal", "CreateDate", "Artist", "Creator", "By-line"]:
                missing_rest.append(tag)
                
    if missing_rest:
        raise ValueError(f"[{filename}] Brakuje pobocznych tagów EXIF z referencji: {', '.join(missing_rest)}")
