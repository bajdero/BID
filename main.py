import os 
import io
from typing import Literal
# import PIL
from PIL import Image, ImageCms, ExifTags, ImageTk
from PIL.PngImagePlugin import PngInfo
# import numpy as np
# from matplotlib import cm
import logging
import _tkinter
import tkinter as tk
from tkinter import ttk
import json
import datetime
# from time import sleep

from threading import Thread
# from queue import Queue
# from enum import Enum, auto

debug_level = logging.INFO


def image_convert_to_srgb(img:Image) -> Image:
    """Zmienia przestrzeń obrasu na sRGB i bedąc szczerym nie wiem jak to robi

    Args:
        img (Image): Obraz o dowolnej przestrzeni barwowej

    Returns:
        Image: Obraz w przestrzeni sRGB
    """    
    '''Convert PIL image to sRGB color space (if possible)'''
    logger.debug("konwertuje zdjecie na sRGB")
    icc = img.info.get('icc_profile', '')
    if icc:
        io_handle = io.BytesIO(icc)     # virtual file
        src_profile = ImageCms.ImageCmsProfile(io_handle)
        dst_profile = ImageCms.createProfile('sRGB')
        img = ImageCms.profileToProfile(img, src_profile, dst_profile)
    return img

def print_exif_ifd0(exif:Image.Exif) -> None:
    """W selach sprawdzaniowo/edukacyjnych printuje root exifa

    Args:
        exif (Image.Exif): Obraz którego exif chcemy sprawdzić 
    """    
    for key, val in exif.items():
            if key in ExifTags.TAGS and ExifTags.TAGS[key]:
                print(f'{key}|{ExifTags.TAGS[key]}: {val}')

def print_exif_all(exif:Image.Exif) -> None:
    """W celach sprawdzaniowo/edukacyjnych. Wyświatla cały znany exif, łącznie z rootem

    Args:
        exif (Image.Exif): Obraz którego exif chcemy sprawdzić 
    """    
    IFD_CODE_LOOKUP = {i.value: i.name for i in ExifTags.IFD}
    for tag_code, value in exif.items():

        # if the tag is an IFD block, nest into it
        if tag_code in IFD_CODE_LOOKUP:

            ifd_tag_name = IFD_CODE_LOOKUP[tag_code]
            print(f"IFD '{ifd_tag_name}' (code {tag_code}):")
            ifd_data = exif.get_ifd(tag_code).items()

            for nested_key, nested_value in ifd_data:

                nested_tag_name = ExifTags.GPSTAGS.get(nested_key, None) or ExifTags.TAGS.get(nested_key, None) or nested_key
                print(f"-{nested_key} | {nested_tag_name}: {nested_value}")
        else:
            # root-level tag
            print(f"{tag_code} | {ExifTags.TAGS.get(tag_code)}: {value}")

def image_resize(img:Image.Image, 
                 longer_side = 1600, 
                 resamle = Image.LANCZOS, 
                 method:Literal['longer', 'width', 'height'] = "longer",
                 reducing_gap = None) -> Image:
    """Skaluje obraz do dłuzszego boku

    Args:
        img (Image): Obraz do skalowania
        longer_side (int, optional): Długość dłuższego boku w px. Defaults to 1600.
        resamle (_type_, optional): uzywana metoda resamplingu. Defaults to Image.LANCZOS.
        method (str): Która krawedz ma być pomniejszona

    Returns:
        Image: Zwaca przeskalowany obraz
    """    
    logger.debug(f"Przycinam zdjęcie do {longer_side}px")

    if method == "longer":
        crop_ratio = longer_side/max(img.size)
    elif method == "width":
        crop_ratio = longer_side/img.width
    elif method == "height":
        crop_ratio = longer_side/img.height

    new_width = int(img.width*crop_ratio)
    new_height = int(img.height*crop_ratio)
    output = img.resize((new_width,new_height), resample=resamle, reducing_gap=reducing_gap)

    return output


def image_change_alpha(img:Image.Image, alpha:int | float) -> Image:
    """Skaluje kanał aplha obrazu. Wydaje mi się że obraz musi mieć już kanał alpha

    Args:
        img (Image): Obraz z kanałem alpha
        alpha (int | float): procent przejżystości

    Returns:
        Image: Obraz z nowym kabałem
    """    
    alpha_factor = alpha/100
    old_alpha = img.getchannel('A')
    new_alpha = old_alpha.point(lambda i: int(i*alpha_factor))
    img.putalpha(new_alpha)
    return img

def exif_cleaf_from_tiff(exif:Image.Exif) -> Image.Exif:
    """Czyści exif z syfu który pozostał po kompresji fiff deflacja z predykcją. Nie wywali się jak któregos taga nie bedzie

    Args:
        exif (Image.Exif): exif obrazu

    Returns:
        Image.Exif: czysciutki exif
    """    
    logger.debug("Czyszczę exif")
    exif_to_pop = [
        273,    #StripOffsets
        279,    #StripByteCounts
        269,    #DocumentName
        317,    #Predictor
        259,    #Compression
        258,    #BitsPerSample
        262,    #PhotometricInterpretation
        277,    #SamplesPerPixel
        278,    #RowsPerStrip
        339,    #SampleFormat
        284,    #PlanarConfiguration
    ]
    for key in exif_to_pop:
        try:
            exif.pop(key)
        except KeyError:
            # print(f"Nie ma takich zwierząt jak {key}:{ExifTags.TAGS[key]}")
            pass
    
    return exif

class SourceState:
    NEW = 'new'
    PROCESSING = 'processing'
    OK = 'ok'
    ERROR = 'error'

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Otwieram ustawienia. 
        # Zdecydowanie wywali się jak nie bdzie pliku
        try:
            with open('settings.json', 'r') as f:
                self.settings = json.load(f)
            logger.debug("Wczytano opcję")
        except Exception as e:
            logger.critical(f"Nie udało się wczytać opcji! | {e}")
            exit()
        
        # Otwieram ustawienia exportu. 
        # Zdecydowanie wywali się jak nie bedzie
        try:
            with open('export_option.json', 'r') as f:   
                self.export_settings = json.load(f)
            logger.debug("Wczytano szablon eksportu")
        except:
            logger.critical("Nie udało się wczytać szablonu exportu!")
            exit()
        
        # Ustawianie ściażki source i export. 
        self.change_source_folder(self.settings["source_folder"])
        self.change_export_folder(self.settings["export_folder"])

        # Sprawdzanie/Tworzenie sorce folder i Tworzenie/sprawdzanie jego zawartości
        if not os.path.exists(self.source_folder):
            logger.warning("Tworzę folder Source")
            os.mkdir(self.source_folder)
        if os.path.isfile('source_dict.json'):
            logger.info("Wczytuję danę o source")
            with open('source_dict.json', 'r', encoding='utf-8') as f:
                self.source_dict = json.load(f)
            self.update_source_dict()
        else:
            logger.warning("Tworzę dane o source")
            self.source_dict = self.create_source_dict()
            self.save_source_dict()

        # Sprawdzanie/Tworzenie exportu
        if not os.path.exists(self.export_folder):
            os.mkdir(self.export_folder)
        for deliver in self.export_settings:
            path = os.path.join(self.settings["export_folder"], deliver)
            if not os.path.exists(path):
                os.mkdir(path)

        self.source_prev = PrevWindow(self)
        self.source_prev.grid(column=0, row=0)

        self.source_tree = SourceTree(self)
        self.source_tree.grid(column=0, row=1)
        self.source_tree.update_tree(self.source_dict)

        self.export_prev = PrevWindow(self)
        self.export_prev.grid(column=1, row=0)

        # larger_size = 1200

        """
        self.raw_photo: Image.Image
        self.raw_photo = Image.open('test.tif', 'r')
        self.raw_exif = self.raw_photo.getexif()
        exif = exif_cleaf_from_tiff(self.raw_exif)

        exif[0x0001] = 'R98'    #InterpolIndex sRGB
        exif[0x00fe] = 0x1      #SubfileType 0x0 - full resolution image 0x1 - Reduced-resolution image
        exif[0x0106] = 2        #PhotometricInterpretation RGB
        exif[0x0112] = 0        #Orientation Horizontal
        exif[0x0103] = 7        #Compression JPEG
        exif[0xc68b] = 'orginalRaw'   #orginalRawFileName

        exif[0x013b] = 'JA'     #Artist
        exif[0x010d] = 'tytul'  #DocumentName
        exif[0x010e] = "opis"#ImageDescription w windowsie widziane jako tytuł i temat

        exif[0xc71b] = '2024:03:06 10:10:00' #PreviewDateTime

        resized_photo: Image
        resized_photo = image_resize(self.raw_photo, 1200)
        # resized_photo = self.raw_photo.resize((new_width,new_height), resample=Image.LANCZOS)

        exif[256] = resized_photo.width
        exif[257] = resized_photo.height

        self.img_conv: Image
        self.img_conv = image_convert_to_srgb(resized_photo)
        # self.img_conv.save('export_test_1.jpg', 
        #                    format = 'JPEG', 
        #                    optimize = True,
        #                    quality = "web_high", 
        #                    exif=exif)
        
        self.full_logo = Image.open('g1.png')
        logo_longer = 200
        # blured_img = self.full_logo.filter(ImageFilter.SMOOTH)
        croped_logo = image_resize(self.full_logo, 250, resamle=Image.NEAREST)
        # logo_crop_ratio = logo_longer/max(self.full_logo.size)
        # logo_width = int(self.full_logo.width*logo_crop_ratio)
        # logo_height = int(self.full_logo.height*logo_crop_ratio)
        # croped_logo = self.full_logo.resize((logo_width, logo_height), resample=Image.NEAREST)
        # croped_logo.show()
        # croped_logo = croped_logo.filter(ImageFilter.MaxFilter)
        croped_logo = image_change_alpha(croped_logo, 180)
        

        x_offset = 30
        y_offset = 50

        logo_layer = Image.new("RGBA", self.img_conv.size)
        logo_layer.paste(croped_logo, (self.img_conv.width-x_offset-croped_logo.width, 
                                       self.img_conv.height-y_offset-croped_logo.height))

        self.img_conv.putalpha(255)
        to_save = Image.new("RGBA", self.img_conv.size)
        to_save = Image.alpha_composite(to_save, self.img_conv)
        to_save = Image.alpha_composite(to_save, logo_layer)

        to_save = to_save.convert("RGB")
        to_save.show()

        to_save.save('export_test_1.jpg', 
                    format = 'JPEG', 
                    optimize = True,
                    quality = 90, 
                    exif=exif)
        
        # self.new_img = Image.open('export_test_1.jpg')
        # exif = self.new_img.getexif()
        """
        self.active_scaning = None
        self.find_new = False

        self.update_source_thred = None
        self.update_source()

        self.scan_photos()

    def scan_photos(self):
        if self.active_scaning is None:
            for index, _ in enumerate(self.source_dict):
                first_folder = list(self.source_dict)[index]
                if len(self.source_dict[first_folder]) > 0:
                    first_photo = list(self.source_dict[first_folder])[0]
                    break
            else:
                logger.error("Scna_photo nie znalazł żadnego zdjęcia do skanowania!")
                return
            
            self.active_scaning = [index, 0]
        
            # print(first_folder, first_photo)

            process_thred = Thread(target=self.process_photo, args=(first_folder, first_photo), daemon=True)
            process_thred.start()

    def process_photo(self, folder:str, photo:str):
        next_thread = Thread(target=self.process_next_photo, args=())
        if self.source_dict[folder][photo]['state'] == SourceState.NEW:
            logger.info(f"Obrabiam zdjęcie {folder} {photo}")
            self.source_tree.change_tag(folder, photo, SourceState.PROCESSING)

            now = datetime.datetime.now()

            ###### MIĘSKO! 
            path = self.source_dict[folder][photo]['path']

            # Ładowanie zdjęcia
            raw_photo: Image.Image
            try:
                raw_photo = Image.open(path, 'r')
            except Exception as e:
                msg = f"Nie udało się otworzyć zdjęcia '{path}' | {e}"
                logger.error(msg)
                self.source_dict[folder][photo]['state'] = SourceState.ERROR
                self.source_tree.change_tag(folder, photo, self.source_dict[folder][photo]['state'])
                self.source_dict[folder][photo]['error_msg'] = msg
                next_thread.start()
                return

            # Pobieranie i czyszczenie exifów
            try:
                raw_exif = raw_photo.getexif()
                exif = exif_cleaf_from_tiff(raw_exif)
            except Exception as e:
                msg = f"Nie udało się otworzyć exifów '{path}' | {e}"
                logger.error(msg)
                self.source_dict[folder][photo]['state'] = SourceState.ERROR
                self.source_tree.change_tag(folder, photo, self.source_dict[folder][photo]['state'])
                self.source_dict[folder][photo]['error_msg'] = msg
                next_thread.start()
                return

            # Dodawanie niektóeych informacji do EXIF
            exif[0x0001] = 'R98'    #InterpolIndex sRGB
            exif[0x00fe] = 0x1      #SubfileType 0x0 - full resolution image 0x1 - Reduced-resolution image
            exif[0x0106] = 2        #PhotometricInterpretation RGB
            exif[0x0112] = 0        #Orientation Horizontal
            # exif[0x0103] = 7        #Compression JPEG
            # exif[0xc68b] = photo   #orginalRawFileName

            exif[0x013b] = folder.encode('utf-8')     #Artist
            # exif[0x010d] = 'YAPA2024'  #DocumentName
            # exif[0x010e] = "YAPA2024"   #ImageDescription w windowsie widziane jako tytuł i temat

            exif[0xc71b] = now.strftime('%Y:%m:%d %H:%M:%S') #PreviewDateTime

            # jaka oriętacja zdjęcia
            if raw_photo.width >= raw_photo.height:
                orientation = 'vertical'
            else:
                orientation = 'horizontal'

            # Export zdjęcia dla każdej metody
            for deliver in self.export_settings:
                # Jeżeli jest key "ratio", to ten delivery akceptuje tylko i wyłącznie tego typu aspect ratio
                try:
                    aspectrs = self.export_settings[deliver]['ratio']
                    logger.debug(f"Wykryłem ograniczenie dla aspect ratio. {deliver} {aspectrs}")
                    tmp_ratio = raw_photo.width / raw_photo.height
                    tmp_ratio = round(tmp_ratio, 2)
                    logger.debug(f"Aspect tario dla {photo} to {tmp_ratio}")
                    if tmp_ratio not in aspectrs:
                        continue
                except KeyError:
                    pass
                # if deliver == "lzp":
                #     tmp_ratio = raw_photo.width / raw_photo.height
                #     tmp_ratio = round(tmp_ratio, 2)
                #     # print(tmp_ratio)
                #     if tmp_ratio not in [0.8, 1.25]:
                #         break
                # Skalowanie zdjęcia
                resized_photo: Image.Image
                resize_px = self.export_settings[deliver]['size']
                try:
                    resized_photo = image_resize(raw_photo, resize_px)
                except Exception as e:
                    msg = f"Nie udało się przeskalować zdjęcia zdjęcia '{path}' w {deliver} | {e}"
                    logger.error(msg)
                    self.source_dict[folder][photo]['state'] = SourceState.ERROR
                    break    

                # Dodawnie exif o rozmiarze, bo nie wiem czy pójdzie z automatu
                exif[256] = resized_photo.width
                exif[257] = resized_photo.height

                # Zmiana przestrzeni barwowej na sRGB
                img_conv: Image.Image
                try:
                    img_conv = image_convert_to_srgb(resized_photo)
                except Exception as e:
                    msg = f"Nie udało się zmienić przestrzeni barwowej '{path}' w {deliver} | {e}"
                    logger.error(msg)
                    self.source_dict[folder][photo]['state'] = SourceState.ERROR
                    break 

                # Odczytywanie logo
                path = os.path.join(self.settings['source_folder'], 
                                    folder, 
                                    'logo.png')
                        
                try:
                    full_logo = Image.open(path)
                except Exception as e:
                    msg = f"Nie udało się odczytać logo '{path}' w {deliver} | {e}"
                    logger.error(msg)
                    self.source_dict[folder][photo]['state'] = SourceState.ERROR
                    break 

                # Nakładanie logo
                resize_px = self.export_settings[deliver]['logo'][orientation]['size']
                croped_logo: Image.Image
                try:
                    # Skalownie logo
                    croped_logo = image_resize(full_logo, resize_px, resamle=Image.NEAREST)

                    croped_logo = image_change_alpha(croped_logo, 
                                                    alpha=self.export_settings[deliver]['logo'][orientation]['opacity'])

                    # ofsetowanie logo względem dolnej prawej krawedzi
                    x_offset = self.export_settings[deliver]['logo'][orientation]['x_offset']
                    y_offset = self.export_settings[deliver]['logo'][orientation]['y_offset']

                    # Nakłądnie
                    logo_layer = Image.new("RGBA", img_conv.size)
                    logo_layer.paste(croped_logo, (img_conv.width- x_offset-croped_logo.width, 
                                                img_conv.height-y_offset-croped_logo.height))

                    img_conv.putalpha(255)
                    to_save = Image.new("RGBA", img_conv.size)
                    to_save = Image.alpha_composite(to_save, img_conv)
                    to_save = Image.alpha_composite(to_save, logo_layer)
                except Exception as e:
                    msg = f"Nie udało się nałożyć logo na {folder} {photo}' w {deliver} | {e}"
                    logger.error(msg)
                    self.source_dict[folder][photo]['state'] = SourceState.ERROR
                    break
                # Usuwanie kanalu alpha
                to_save = to_save.convert("RGB")
                # to_save.show()
                
                # Nadawanie nowej nazwy pliku
                created_date: str
                created_date = self.source_dict[folder][photo]['created']
                created_date = created_date.replace(' ', '_').replace(':', '-')
                orginal_file = photo.split('.')[0]

                export_name = f"YAPA{created_date}_{folder.replace(' ', '_')}_{orginal_file}"

                # TODO: Być może tu będzie miejscena obsuwę 
                
                if self.export_settings[deliver]['format'] == "JPEG":
                    export_name +='.jpg'
                    # exif[0x0103] = 7        #Compression JPEG
                elif self.export_settings[deliver]['format'] == "PNG":
                    export_name +='.png'
                    png_metadata = PngInfo()
                    png_metadata.add_text("Artist", folder.encode('utf-8'))
                    png_metadata.add_text("OrginalRawFileName", photo)
                    png_metadata.add_text("DocumentName", 'YAPA2024')
                    png_metadata.add_text("ImageDescription", 'YAPA2024')
                    png_metadata.add_text("DateTimeOrginal", self.source_dict[folder][photo]['created'])
                    png_metadata.add_text("PreviewDateTime", now.strftime('%Y:%m:%d %H:%M:%S'))
                else:
                    msg = f"Nieznany format delivery {folder} {photo} '{path}' w {deliver}"
                    logger.error(msg)
                    self.source_dict[folder][photo]['state'] = SourceState.ERROR
                    break 

                export_path = os.path.join(self.settings['export_folder'], 
                                           deliver, 
                                           export_name)

                try:
                    if self.export_settings[deliver]['format'] == "JPEG":
                        to_save.save(export_path, 
                                    format = 'JPEG', 
                                    optimize = True,
                                    quality = self.export_settings[deliver]['quality'])
                        # exif=exif
                    elif self.export_settings[deliver]['format'] == "PNG":
                        to_save.save(export_path, 
                                    format = 'PNG', 
                                    optimize = True,
                                    compress_level = self.export_settings[deliver]['quality'])
                        #pnginfo = png_metadata
                    self.source_dict[folder][photo]['exported'][deliver] = export_path
                except Exception as e:
                    msg = f"Nie udało się zapisać zdjęcia {folder} {photo} '{path}' w {deliver} | {e}"
                    logger.error(msg)
                    self.source_dict[folder][photo]['state'] = SourceState.ERROR
                    break    

            ###### KONIEC MIĘSKA!
            self.source_dict[folder][photo]['state'] = SourceState.OK
            # self.source_tree.change_tag(folder, photo, SourceState.OK)
            # self.process_next_photo()
        # else:
            # self.process_next_photo()
        self.source_tree.change_tag(folder, photo, self.source_dict[folder][photo]['state'])
        next_thread.start()

        
    def process_next_photo(self):
        folder = list(self.source_dict)[self.active_scaning[0]]
        # inkrementowanie pliku
        self.active_scaning[1] += 1
        if self.active_scaning[1] >= len(self.source_dict[folder]):
            self.active_scaning[0] += 1
            self.active_scaning[1] = 0
            try:
                folder = list(self.source_dict)[self.active_scaning[0]]
            except IndexError:
                self.active_scaning = None
                return
        
        # if self.active_scaning[1] >= len(self.source_dict[folder]) and len(self.source_dict[folder]) > 0:
        #     self.active_scaning[0] += 1
        #     self.active_scaning[1] = 0
        #     if self.active_scaning[0] >= len(self.source_dict):
        #         self.active_scaning = None
        #         return
        folder = list(self.source_dict)[self.active_scaning[0]]
        try:
            photo = list(self.source_dict[folder])[self.active_scaning[1]]
            process_thred = Thread(target=self.process_photo, args=(folder, photo), daemon=True)
            process_thred.start()
        except IndexError:
            self.process_next_photo()

    def update_source(self):
        if self.update_source_thred is not None:
            if self.update_source_thred.is_alive():
                logger.warning("Nie zakończyłem aktualizowanie source, a przyszedł już czas na kolejne")
                self.after(1000, self.update_source)
                return
            self.update_source_thred = Thread(target=self.update_source_threding, daemon=True)
            self.update_source_thred.start()
        else:
            self.update_source_thred = Thread(target=self.update_source_threding, daemon=True)
            self.update_source_thred.start()

    def update_source_threding(self):
        logger.debug("Cykliczne sprawdzanie source")
        try:
            self.update_source_dict()
            self.source_tree.update_tree(self.source_dict)
            if self.find_new:
                self.scan_photos()
                self.find_new = False
            self.after(1000, self.update_source)
        except Exception as e:
            logger.error(f"Nie udało się wykonać cyklicznego sprawdzenia sorce | {e}")
            self.after(1000, self.update_source)
    
    def change_source_folder(self, folder:str) -> None:
        logger.info(f"Podano nowy folder żródłowy {folder}")
        self.source_folder = folder

    def change_export_folder(self, folder:str) -> None: 
        logger.info(f"Podano nowy folder docelowy {folder}")
        self.export_folder = folder
    
    def create_source_item(self, root, folder, file) -> dict:
        

        stats = os.stat(os.path.join(root, file))
        path = os.path.join(root, file)
        exif = Image.open(path).getexif()
        # if file == 'DSC07205.tif':
        #     print_exif_all(exif)
            # print(exif[34665])
        #TODO: No nie... no po prostu nie nie
        if exif:
            try:
                created = exif[0x9003] #DateTimeOrginal
            except KeyError:
                try:
                    created = exif.get_ifd(34665)[0x9003] #DateTimeOrginal z IFD
                except KeyError:
                    logger.warning(f"Zdjęcie {folder} {file} nie ma informacji o dacie w exifie")
                    created = datetime.datetime.fromtimestamp(int(stats.st_mtime), datetime.UTC).strftime('%Y:%m:%d %H:%M:%S')
        else:
            logger.error(f"Nie można odczytać exif w {folder} {file}")
            created = "xxx:xx:xx xx:xx:xx"
        
        size = f'{stats.st_size / 1024000:.02f} MB'
        output = {
            "path": path,
            'state': SourceState.NEW,
            'exported': {},
            'size': size,
            'created': created
        }

        return output

    def create_source_dict(self) -> dict:
        logger.debug("Tworzę source_dict")
        output = dict()
        root_folder = os.walk(self.source_folder)
        for root, dirs, files in root_folder:
            if root == self.source_folder:
                continue
            else:
                folder_name = root.split('\\')[-1]
                output[folder_name] = {}
                if 'logo.png' not in files:
                    logger.error(f"Nie odnaleziono loga w folderze {folder_name}")
                for file in files:
                    if file == 'logo.png':
                        continue

                    output[folder_name][file] = self.create_source_item(root, folder_name, file)
                    # stats = os.stat(os.path.join(root, file))
                    # # print(stats)
                    # size = f'{stats.st_size / 1024000:.02f} MB'
                    # output[folder_name][file] = {
                    #     "path": os.path.join(root, file),
                    #     'state': SourceState.NEW,
                    #     'exported': {},
                    #     'size': size,
                    #     'created': datetime.datetime.fromtimestamp(int(stats.st_mtime), datetime.UTC).strftime('%Y:%m:%d %H:%M:%S'), 
                    #     'created_datetime': stats.st_mtime
                    # }
        
        return output

    def update_source_dict(self):
        """aktualizuje informacje o tym co jest w source
        """        
        logger.debug("Aktualizuję source_dict")
        self.find_new = False
        root_folder = os.walk(self.source_folder)
        for root, dirs, files in root_folder:
            if root == self.source_folder:
                continue
            else:
                folder_name = root.split('\\')[-1]
                if folder_name not in self.source_dict.keys():
                    logger.info(f"Wykryem nowy folder '{folder_name}'")
                    self.source_dict[folder_name] = {}
                if 'logo.png' not in files:
                    logger.error(f"Nie odnaleziono loga w folderze {folder_name}")
                for file in files:
                    if file == 'logo.png':
                        continue
                    if file not in self.source_dict[folder_name].keys():
                        logger.info(f"Wykryłem nowy plitk w folderze '{folder_name}' | '{file}'")
                        self.find_new = True
                        self.source_dict[folder_name][file] = self.create_source_item(root, folder_name, file)
                        # stats = os.stat(os.path.join(root, file))
                        # size = f'{stats.st_size / 1024000:.02f} MB'
                        # self.source_dict[folder_name][file] = {
                        #     "path": os.path.join(root, file),
                        #     'state': SourceState.NEW,
                        #     'exported': {},
                        #     'size': size,
                        #     'created': datetime.datetime.fromtimestamp(int(stats.st_mtime), datetime.UTC).strftime('%Y:%m:%d %H:%M:%S'), 
                        #     'created_datetime': stats.st_mtime
                        # }
        self.save_source_dict()
        
    def save_source_dict(self):
        with open('source_dict.json', 'w', encoding='utf-8') as f:
            out = json.dumps(self.source_dict, indent= 4, ensure_ascii=False)
            f.write(out)

class PrevWindow(tk.Frame):
    def __init__(self, root:MainApp) -> None:
        super().__init__(root)
        self.root = root
        self.size = 300

        with Image.open('src/default_prev.png') as img:
            self.tk_img = ImageTk.PhotoImage(img)

        self.img_path = None

        self.photo_canvas = tk.Canvas(self, width=self.size, height=self.size, bg="gray")
        self.photo_canvas.pack()

        self.img_canvas = self.photo_canvas.create_image(self.size/2, self.size/2, image=self.tk_img)

    def change_img(self, img_path:str) -> None:
        self.img_path = img_path

        if os.path.isfile(self.img_path):
            with Image.open(self.img_path) as img:
                img = image_resize(img, self.size, Image.NEAREST, reducing_gap=1.5)
                self.tk_img = ImageTk.PhotoImage(img)

                self.img_canvas = self.photo_canvas.create_image(self.size/2, self.size/2, image=self.tk_img)
        else:
            logger.error(f"Nie ma pliku {self.img_path}")

class SourceTree(tk.Frame):
    def __init__(self, root:MainApp) -> None:
        super().__init__(root)
        self.root = root

        self.source_tree = ttk.Treeview(self, 
                                        columns=['rozmiar', 'date', 'path'],
                                        displaycolumns=['rozmiar', 'date'],
                                        height=23, 
                                        selectmode='browse')
        self.source_tree.column('#0', width=200)
        self.source_tree.column('rozmiar', width=80)
        self.source_tree.column('date', width=120)
        self.source_tree.heading('#0', text="Nazwa", anchor=tk.W)
        self.source_tree.heading('rozmiar', text="Rozmiar", anchor=tk.W)
        self.source_tree.heading('date', text="Data", anchor=tk.W)

        self.source_tree.tag_configure(SourceState.NEW,         background= "light gray")
        self.source_tree.tag_configure(SourceState.PROCESSING,  background='sky blue')
        self.source_tree.tag_configure(SourceState.OK,          background='pale green')
        self.source_tree.tag_configure(SourceState.ERROR,       background='coral')

        # self.source_tree.bind('<<TreeviewSelect>>', self.tree_slect)
        self.source_tree.bind('<Double-1>', self.tree_slect)
        self.source_tree.pack()

    def change_tag(self, folder, photo, tag:SourceState):
        """Zmienia tag zdjęcia

        Args:
            folder (_type_): autor
            photo (_type_): nazwa zdjęcia
            tag (SourceState): na jaki tag
        """        
        logger.debug(f"Zmieniam tag zdjęcia {folder} {photo} na {tag}")
        self.source_tree.item(f'{folder}_{photo}', tag=tag)

    def tree_slect(self, event):
        """Obsługa eventu od klikniecia/podwójnego klikniecia

        Args:
            event (_type_): _description_
        """        
        tree = event.widget
        # slelected = self.source_tree.selection()
        try:
            path = tree.item(tree.selection()[0])['values'][-1]
            update_thred = Thread(target=self.root.source_prev.change_img, args=(path, ), daemon=True)
            update_thred.start()
            # self.root.source_prev.change_img(path)
        except _tkinter.TclError as e:
            logger.error(f"Nie ma tego co zaznaczyłeś | {e}")
            return
        # if slelected[0] in self.root.source_dict.keys():
        #     return
        # print(slelected['path'])
    
    def update_tree(self, source_dict:dict):
        """aktualizuje source tree view. tak na prawdę to tylko dadaje do tree, co jest w sumie słabe ale

        Args:
            source_dict (dict): sorce dict
        """        
        # self.source_tree.delete(*self.source_tree.get_children())
        for folder in source_dict:
            try:
                self.source_tree.insert("", 'end', folder, text=folder, values=(f"{len(source_dict[folder])} zdjęć",))
            except _tkinter.TclError:
                self.source_tree.item(folder, values=(f"{len(source_dict[folder])} zdjęć",))
            for file in source_dict[folder]:
                size = source_dict[folder][file]['size']
                date = source_dict[folder][file]['created']
                path = source_dict[folder][file]['path']
                tag = source_dict[folder][file]['state']
                try:
                    #TODO: ten id to fajnie aby się jakoś randomowo losowa i do tego aby jeszce się sprawdzał czy na pewno jest unikatowy. 
                    self.source_tree.insert(folder, 'end', id=f'{folder}_{file}', text=file, values=[size, date, path],
                                            tags=tag)
                except _tkinter.TclError:
                    continue
                    



if __name__ == "__main__":
    logger = logging.getLogger("Yapa_CM")
    logger.setLevel(debug_level)

    formatter_log = logging.Formatter("%(asctime)s | %(levelname)-8s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")

    handler_log = logging.StreamHandler()
    handler_log.setLevel(debug_level)
    handler_log.setFormatter(formatter_log)
    logger.addHandler(handler_log)

    log_path = datetime.datetime.now().strftime('%Y-%m-%d_%H_%M_%S')
    log_path = f'{log_path}.log'
    log_path = os.path.join('logs', log_path)
    if not os.path.exists('logs'):
        os.mkdir('logs')
    log_fh = logging.FileHandler(log_path, encoding='utf-8')
    log_fh.setLevel(debug_level)
    log_fh.setFormatter(formatter_log)
    logger.addHandler(log_fh)

    logger.info("Rozpoczecie programu")

    main_window = MainApp()

    main_window.mainloop()


