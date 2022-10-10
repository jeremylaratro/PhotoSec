import argparse
import os
import subprocess
import sys
import exif
import signal


class Security:
    # class for file renaming and scrubbing functions

    def __init__(self, name):
        self.name = name

    def get_dir(self):
        print("Make sure that directory ends with '/''")
        directory = input("Enter the directory: ")
        file_path = os.path.join(os.path.dirname(__file__), directory)
        return file_path

    def get_photos(self):
        file_path = self.get_dir()
        photos = ['.jpg', '.jpeg', '.png', '.gif']
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                return file_path, file
            else:
                continue

    def signal_handler(sig, frame):
        choice = input("Are you sure you want to exit? (y/n): ")
        if choice.lower() == 'y':
            sys.exit(0)
        else:
            pass

    def continue_q(self):
        # prompt user to continue
        # To-Do: add a continue same function option
        print("Would you like to continue? (y/n): ")
        choice = input().lower()
        if choice == 'y':
            Security.main(self)
        else:
            exit()

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

        ''')
        self.main()

    def rename_cli(self):
        directory = Security.get_dir(self)
        # prompt user to enter directory where files are stored
        # directory = input("Enter the directory: ")
        name = input(
            "Enter the file name you'd like to use (ie: RL0, RL1, RL2, etc). \nThe syntax will consist of the string you enter, plus an increasing number. \nIf you enter a number, the increasing number will be added after that (ie PHOTO2 --> PHOTO21, PHOTO22, etc): ")
        file_path = os.path.join(os.path.dirname(__file__), directory)
        # number each file in the directory starting with 1
        i = 1
        # loop through each file in the directory
        for file in os.listdir(file_path):
            # get the file extension
            ext = os.path.splitext(file)[-1]
            # rename the file
            os.rename(os.path.join(file_path, file), os.path.join(file_path, name + str(i)) + ext)
            # increment i by 1
            i += 1
        print("Files renamed successfully!")
        self.continue_q()

    def clear_cli(self):
        directory = Security.get_dir(self)
        file_path = os.path.join(os.path.dirname(__file__), directory)
        photos = [".jpg", ".jpeg", ".png", ".gif"]
        i = 0
        cl = 0
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                with open(file_path + file, 'br+') as f:
                    img = exif.Image(f)
                    if img.has_exif:
                        img.delete_all()
                        cl += 1
                        with open(file_path + file, 'wb') as mf:
                            mf.write(img.get_file())
                    else:
                        cl += 0
                        pass
                i += 1
        print("EXIF data cleared from " + str(cl) + " files!")
        self.continue_q()

    def check_geo(self):
        file_path, file = Security.get_photos(self)
        i = 0
        gps_data = []
        for file in os.listdir(file_path):
            with open(file_path + file, 'br+') as f:
                img = exif.Image(f)
                att = img.list_all()
                if i < len(os.listdir(file_path)):
                    if '_gps_ifd_pointer' in att:
                        print("GPS data found in file: " + file)
                        gps_data.append('File name: ' + file + ' | (LAT, LONG)')
                        gps_data.append(img.gps_latitude + img.gps_longitude)
                        i += 1
                    else:
                        print("No GPS data found in file: " + file)
                        i += 1
        print(gps_data)
        self.continue_q()

    def image_analysis(self):
        print("This feature analyzes an image using exiftool, binwalk, strings,"
              " and the exif module, and outputs the results to a text file for analysis."
              "This features currently only works for single images at a time. ")
        file_path, file = Security.get_photos(self)
        i = 0
        with open(file_path + file, 'br+') as f:
            img = exif.Image(f)
            with open('../ExifData/' + str(file) + '_EXIF_data.txt', 'w') as txt:
                txt.write('Image Analysis: \n')
                arg1 = file_path + file
                attr = img.list_all()
                txt.write('\nEXIF ATTRIBUTES: \n\n')
                txt.write(str(attr) + '\n')
                txt.write('\nEXIFTOOL DATA: \n\n')
                e = subprocess.run(["exiftool %s" % (arg1)], shell=True, text=True, capture_output=True,
                                   universal_newlines=True)
                txt.write(e.stdout)
                txt.write("\nBINWALK DATA: \n\n")
                b = subprocess.run(["binwalk %s" % (arg1)], shell=True, text=True, capture_output=True,
                                   universal_newlines=True)
                txt.write(b.stdout)
                txt.write("\nSTRINGS DATA: \n\n")

                s = subprocess.run(["strings %s" % (arg1)], shell=True, text=True, capture_output=True,
                                   universal_newlines=True)
                txt.write(s.stdout)
            i += 1
        print("Image analysis data successfully output. Data is available in /PhotoSec/ExifData/")
        self.continue_q()

    def main(self):
        # Start the welcome function from security class
        signal.signal(signal.SIGINT, Security.signal_handler)
        m_inp = input(
            "Options: clear EXIF data (c), rename files (r), check for geo data (g), image analysis (a), see usage/get help (h): ").lower()
        if m_inp == "r":
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
            print("Please enter 'r' or 'c'")
            self.main()
