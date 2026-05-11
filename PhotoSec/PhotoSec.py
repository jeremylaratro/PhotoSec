import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import exif
import signal


class Security:
    # class for file renaming and scrubbing functions

    def __init__(self, name):
        self.name = name

    def get_dir(self):
        directory = input("Enter the directory: ")
        file_path = os.path.realpath(os.path.join(os.path.dirname(__file__), directory))
        if not os.path.isdir(file_path):
            print(f"Directory not found: {file_path}")
            return None
        return file_path

    @staticmethod
    def signal_handler(sig, frame):
        choice = input("Are you sure you want to exit? (y/n): ")
        if choice.lower() == 'y':
            sys.exit(0)
        else:
            pass

    def print_help(self):
        print("Usage: ")
        print('''
        This script can be used as a CLI tool (interactive) or via CLI arguments and follow the prompts. \n
         -- To use the CLI tool, run the script without any arguments:
                python3 PhotoSec.py
        -- To use the CLI arguments, the following arguments are currently supported:
                -h or --help for help
                -r or --rename to rename files in a directory
                -c or --clear to clear EXIF data from files in a directory
                -g or --geo to bulk check if images contain GPS/location data
                -a or --analysis to analyze a photo using various tools and output the results to a text file
        -- Errors:
               - Ensure that you are using the proper path
               - Ensure that the file extension is correct. Currently, the file must contain an extension, ie 'file'
               will not work, but file.jpg' will.

        ''')

    def rename_cli(self):
        file_path = self.get_dir()
        if file_path is None:
            return
        name = input(
            "Enter the file name you'd like to use (ie: RL0, RL1, RL2, etc). \nThe syntax will consist of the string you enter, plus an increasing number. \nIf you enter a number, the increasing number will be added after that (ie PHOTO2 --> PHOTO21, PHOTO22, etc): ")
        photos = ['.jpg', '.jpeg', '.png', '.gif']
        files_to_rename = [f for f in os.listdir(file_path)
                           if os.path.isfile(os.path.join(file_path, f))
                           and os.path.splitext(f)[1].lower() in photos]
        print(f"Will rename {len(files_to_rename)} file(s). Continue? (y/n): ", end='')
        if input().lower() != 'y':
            return
        i = 1
        for file in files_to_rename:
            ext = os.path.splitext(file)[-1]
            os.rename(os.path.join(file_path, file), os.path.join(file_path, name + str(i)) + ext)
            i += 1
        print("Files renamed successfully!")

    def clear_cli(self):
        file_path = self.get_dir()
        if file_path is None:
            return
        photos = [".jpg", ".jpeg", ".png", ".gif"]
        i = 0
        cl = 0
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                with open(os.path.join(file_path, file), 'rb') as f:
                    img = exif.Image(f)
                if img.has_exif:
                    img.delete_all()
                    with tempfile.NamedTemporaryFile(delete=False, dir=file_path, suffix='.tmp') as tmp:
                        tmp.write(img.get_file())
                    shutil.move(tmp.name, os.path.join(file_path, file))
                    cl += 1
                i += 1
        print(f"EXIF data cleared from {cl} files!")

    def check_geo(self):
        file_path = self.get_dir()
        if file_path is None:
            return
        photos = ['.jpg', '.jpeg', '.png', '.gif']
        image_files = [f for f in os.listdir(file_path) if f.lower().endswith(tuple(photos))]
        if not image_files:
            print("No image files found in the specified directory.")
            return
        gps_data_t = {}
        gps_data_l = []
        i = 0

        def _dms_to_decimal(dms, ref):
            degrees, minutes, seconds = dms
            decimal = degrees + minutes / 60 + seconds / 3600
            if ref in ('S', 'W'):
                decimal = -decimal
            return decimal

        for file in image_files:
            with open(os.path.join(file_path, file), 'rb') as f:
                img = exif.Image(f)
                img_atts = [img.list_all()]
                for at in img_atts:
                    if '_gps_ifd_pointer' in at:
                        lat = _dms_to_decimal(img.gps_latitude, img.gps_latitude_ref)
                        lon = _dms_to_decimal(img.gps_longitude, img.gps_longitude_ref)
                        gps_data_t[file] = {'LAT': lat, 'LONG': lon}
                        gps_data_l.append(f'File {i}: ' + file)
                        gps_data_l.append(f'LAT: {lat:.6f}, LONG: {lon:.6f}')
                        i += 1
        print(gps_data_l)

    def image_analysis(self):
        print("This feature analyzes an image using exiftool, binwalk, strings,"
              "file, identify, pngcheck, and the exif module. The results are output to a text file."
              "Ensure that all images have a proper extension (ie: .jpg, .png, .gif, etc)."
              "If they don't, use the rename function first. ")
        file_path = self.get_dir()
        if file_path is None:
            return
        photos = ['.jpg', '.jpeg', '.png', '.gif']
        image_files = [f for f in os.listdir(file_path) if f.lower().endswith(tuple(photos))]
        if not image_files:
            print("No image files found in the specified directory.")
            return
        output_dir = os.path.join(os.path.dirname(__file__), 'ExifData')
        os.makedirs(output_dir, exist_ok=True)
        for file in image_files:
            arg1 = os.path.join(file_path, file)
            with open(arg1, 'rb') as f:
                img = exif.Image(f)
            output_path = os.path.join(output_dir, file + '_analysis_.txt')
            with open(output_path, 'w+') as txt:
                txt.write('Image Analysis: \n')
                attr = img.list_all()
                txt.write('\nEXIF ATTRIBUTES: \n\n')
                txt.write(str(attr) + '\n')
                txt.write('\nEXIFTOOL DATA: \n\n')
                try:
                    e = subprocess.run(["exiftool", arg1], text=True, capture_output=True)
                    txt.write(e.stdout)
                except FileNotFoundError as e:
                    txt.write(f"exiftool not found: {e}\n")
                txt.write("\nBINWALK DATA: \n\n")
                try:
                    b = subprocess.run(["binwalk", arg1], text=True, capture_output=True)
                    txt.write(b.stdout)
                except FileNotFoundError as e:
                    txt.write(f"binwalk not found: {e}\n")
                txt.write("\nFILE DATA: \n\n")
                try:
                    b = subprocess.run(["file", arg1], text=True, capture_output=True)
                    txt.write(b.stdout)
                except FileNotFoundError as e:
                    txt.write(f"file not found: {e}\n")
                txt.write("\nIDENTIFY DATA: \n\n")
                try:
                    b = subprocess.run(["identify", arg1], text=True, capture_output=True)
                    txt.write(b.stdout)
                except FileNotFoundError as e:
                    txt.write(f"identify not found: {e}\n")
                txt.write("\nPNG DATA: \n\n")
                try:
                    b = subprocess.run(["pngcheck", arg1], text=True, capture_output=True)
                    txt.write(b.stdout)
                except FileNotFoundError as e:
                    txt.write(f"pngcheck not found: {e}\n")
                txt.write("\nSTRINGS DATA: \n\n")
                try:
                    s = subprocess.run(["strings", arg1], text=True, capture_output=True)
                    txt.write(s.stdout)
                except FileNotFoundError as e:
                    txt.write(f"strings not found: {e}\n")
        print("Image analysis data successfully output. Data is available in /PhotoSec/ExifData/")

    def main(self):
        # Start the welcome function from security class
        signal.signal(signal.SIGINT, Security.signal_handler)
        while True:
            m_inp = input(
                "Options: clear EXIF data (c), rename files (r), check for geo data (g), image analysis (a), see usage/get help (h), quit (q): ").lower()
            if m_inp == 'q':
                sys.exit(0)
            elif m_inp == "r":
                self.rename_cli()
            elif m_inp == "c":
                self.clear_cli()
            elif m_inp == "g":
                self.check_geo()
            elif m_inp == "a":
                self.image_analysis()
            elif m_inp == "h" or m_inp == "help":
                self.print_help()
            else:
                print("Invalid option. Please enter: c (clear), r (rename), g (geo), a (analysis), h (help), q (quit)")
