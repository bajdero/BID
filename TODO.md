# TODO List for BID befor 2026 event

## 1. Naming convention for project

This project should be named BID, which stands for "Best Image Downloader". This name reflects the purpose of the project, which is to provide users with a tool to download, manage, and deliver their images efficiently. The name is simple, memorable, and easy to pronounce, making it an ideal choice for the project.
In project there could be older naming like YAPA, YAPA_CM, but they should be replaced with BID in all documentation, code comments, and user interfaces to maintain consistency and avoid confusion among users.

## 2. Add new information to detaild info panel

In detaild panel, There are important information (bool text), and other exifs. 
In the importatn information there should be: 
- Size
- Date (creation)
- state
- author from EXIF. if exif are non then empty. if exif exist but author is empty, then it should be empty. 
- Pixel size (width x height in pixels)
- Aspect ratio (calculated as width divided by height)

## 3. More option in tree viewe. 
There should be more options in contextr menu (right click) in tree view (source and export). text should be onlu in polish. 
- properties (open windows/linux file properties)
- open in explorer (open file location in file explorer)
- force rewark (on source file forces to rework all export profiles, on export view force to rework only selected export profile)

## 4. export profile wizard. 
There should be export profile wizard, which will guide user through the process of creating export profile. It should be simple and easy to use, with clear instructions and options. The wizard should allow users to select the desired export settings, such: 
- Name
- Export format (JPEG, PNG)
- Export quality (for JPEG from 10 to 100, for PNG from 1 to 9)
- if logo is required to export. If true folders without logo should be skipped. If false, folders without logo should be exported without logo, and coresponding warting log should be added. This photo should be marked in source tree view. 
- logo placment (top left, top right, bottom left, bottom right)
- logo size (small, medium, large)

## 5. UI improvements.
### UX-002: Error messages for user 🎨🎨🎨
- **Status:** Errors only in logs — user sees blank screen
- **Plan:** Add `messagebox.showwarning()` for: missing logo (once per folder, rest in logs), corrupted JSON, processing timeout. Should include mechanism to prevent too frequent popups and multiple windows at once (e.g., one per file)
- **Pattern:** Toast notification — appears for 5s in bottom corner

### UX-004: Status icons in file tree 🎨🎨
- **Status:** Row coloring — subtle, hard to distinguish
- **Plan:** Add icons ●/✓/✗/⏳ before filename + keep background colors
- **Existing TODO:** line 49 `bid/ui/source_tree.py`

### UX-008: Path validation in SetupWizard 🎨
- **Location:** `bid/ui/setup_wizard.py` line 224–247 (`_on_finish`)
- **Status:** Missing check if source ≠ export folder
- **Plan:** Add validation + warning before overwrite

## 6. Errors and code improvments: 

### 6.1 Logo Code Duplication
- `bid/source_manager.py` lines 131, 173, 200 — same logo.png check in 3 places
- **Plan:** Extract `_check_logo_exists(folder_path: Path) -> bool`

### 6.2 OK_OLD Errors
There is some errors: 
logs: 
```
2026-03-10T22:52:26 | ERROR   : Błąd sprawdzania OK_OLD dla test/0Z9A0005.tif: cannot unpack non-iterable float object
...
```

### 6.3 TiffImagePlugin Warnings
- **Status:** Uncached metadata warnings from PIL TiffImagePlugin (tag 33723)
- **logs:**
```
d:\_projekty\YAPA\BID\.venv\Lib\site-packages\PIL\TiffImagePlugin.py:759: UserWarning: Metadata Warning, tag 33723 had too many entries: 2, expected 1
  warnings.warn(
```
- **Location:** `.venv\Lib\site-packages\PIL\TiffImagePlugin.py:759`
- **Plan:** Suppress non-critical warnings or validate TIFF metadata before processing

### 6.4 Missing filename sanitization
- **Location:** `bid/image_processing.py` line 244–245, `bid/source_manager.py`
- **Description:** Export filename built from `folder_name` + `created_date` — without sanitizing special characters
- **Risk:** On Windows, characters `<>:"/\|?*` in folder name → write crash
- **Fix:** `re.sub(r'[<>:"/\\|?*]', '_', filename)`

### 6.5 Path traversal in source_folder
- **Location:** `bid/source_manager.py` `os.walk(source_folder)` — no validation that path does not escape allowed range
- **Risk level:** Low. User sets paths manually, but symlinks could lead outside source
- **Fix:** `os.path.realpath()` + prefix check

## 7 tests

### 7.1 Automatic exif data creation
In automation test, there should be test taht creates exif_reference.json file using exiftool. This file should contain exif data for all test images. Unit test will firstry check if BID is able to read all exif data. exif_reference.json created from exiftool should be use as a referance for unit test. If BID is able to read all exif data correctly, then the test should pass. If BID is not able to read critical exif data (author, creation date), then the test should fail and provide a clear error message to the user. This will help us ensure that BID is able to read and preserve exif data correctly during the export process. If there is aby other exif data that is not critical but is missing, then the test should provide a warning message to the user, but it should not fail the test. it should be expected fails. This will help us identify any potential issues with exif data preservation and allow us to address them in future updates.
There should be config file where user will specify the path to exiftool and the folder where test images are located. The test should be run before the export process and should generate the exif_reference.json file in a specified location.
If exiftool is not available or the test images are not found, the test should mark as failed and provide a clear error message to the user. This will help us identify any issues with the exif data preservation and ensure that the export process is working correctly.
This test is already implemented, but witch static test data. Goal of this point is to make it more dynamic and use exiftool to generate reference data.

### 7.2 Author information preservation
Add test. If autor exist in exif files, then it should be the same in export file. If it is not, then it should be added to export file based ond folder name. This will ensure that the author information is preserved during the export process and can be easily accessed in the exported files.
There should be unit test and regresion test. 