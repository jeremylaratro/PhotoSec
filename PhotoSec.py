import os
import exif
import argparse
import signal
import sys
import subprocess
import pandas as pd
import time


class Security:
    # class for file renaming and scrubbing functions

    def __init__(self, name):
        self.name = name

    def welcome(self):
        print('''
                          Welcome to the CLI PhotoSec utils!  
                                        .---.
                                        |[X]|
                                 _.==._.""""".___~__
                                d __ ___.-''-. _____b
                                |[__]  /."__".\ _   |  
                                |     /  /""\  \ (_)|
                                |     \  \__/  /    |
                                |      \`.__.'/     |
                                \=======`-..-'======/
                                 `-----------------'       
                         
            This script contains functions to bulk clear EXIF data, check for GPS data, and rename files.
            Please note that this program will overwrite the original files.
            Please make sure you have a backup of the files before running this program 
            if you wish to preserve this data; author not responsible for any data loss.
            Author: Jeremy Laratro 
            github.com/jeremylaratro
            Special thanks to Kenneth Leung for the EXIF library (github.com/kennethleungty)   
                         
                         ''')

    def get_dir(self):
        directory = input("Enter the directory: ")
        return directory

    def get_photos(self):
        file_path = os.path.join(os.path.dirname(__file__), directory)
        photos = [".jpg", ".jpeg", ".png", ".gif"]
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                return file

    def signal_handler(sig, frame):
        print('\n Are you sure you want to exit? (y/n)')
        choice = input().lower()
        if choice == 'y':
            sys.exit(0)
        else:
            pass

    def parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-h", "--help", help="help")
        parser.add_argument("-r", "--rename", help="Rename files in a directory", action="store_true")
        parser.add_argument("-c", "--clear", help="Clear EXIF data from files in a directory", action="store_true")
        parser.add_argument("-g", "--geo", help="Bulk check if images contain GPS/location data", action="store_true")
        args = parser.parse_args()
        if args.rename:
            Security.rename_cli(self)
        elif args.clear:
            Security.clear_cli(self)
        elif args.geo:
            Security.check_geo(self)
        elif args.help or not args.rename or not args.clear:
            parser.print_help()

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
                
        ''')

    def rename_cli(self):
        directory = Security.get_dir(self)
        # prompt user to enter directory where files are stored
        # directory = input("Enter the directory: ")
        name = input("Enter the file name you'd like to use (ie: RL0, RL1, RL2, etc): ")
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

    def clear_cli(self):
        directory = Security.get_dir(self)
        # directory = input("Enter the directory where photos are stored: ")
        rename = input("Would you like to rename the files? (y/n): ")
        file_path = os.path.join(os.path.dirname(__file__), directory)
        # create a list of valid extensions
        photos = [".jpg", ".jpeg", ".png", ".gif"]
        # loop through each file in the directory
        for file in os.listdir(file_path):
            # check if the file has a valid extension
            if file.endswith(tuple(photos)):
                # open the files in binary / read mode
                with open(file_path + file, 'br+') as f:
                    # initialize the exif library
                    img = exif.Image(f)
                    # check if the image contains exif data
                    if img.has_exif:
                        # remove the exif data if so
                        img.delete_all()
                        # save the file
                        with open(file_path + file, 'wb') as mf:
                            mf.write(img.get_file())
                        # rename the files if option was chosen
                        if rename == "y":
                            Security.rename_cli(self)
                    else:
                        continue

    def check_geo(self):
        directory = Security.get_dir(self)
        file_path = os.path.join(os.path.dirname(__file__), directory)
        photos = [".jpg", ".jpeg", ".png", ".gif"]
        i = 0
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                with open(file_path + file, 'br+') as f:
                    img = exif.Image(f)
                    att = img.list_all()
                    if i < len(os.listdir(file_path)):
                        if '_gps_ifd_pointer' in att:
                            print("GPS data found in file: " + file)
                            i += 1
                        else:
                            print("No GPS data found in file: " + file)
                            continue
                    else:
                        break

    def image_analysis(self):
        directory = Security.get_dir(self)
        file_path = os.path.join(os.path.dirname(__file__), directory)
        photos = [".jpg", ".jpeg", ".png", ".gif"]
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                with open(file_path + file, 'br+') as f:
                    img = exif.Image(f)
                    with open('exif_data5.txt', 'w') as txt:
                        txt.write('Image Analysis: \n')
                        arg1 = file_path + file
                        attr = img.list_all()
                        txt.write('\nEXIF ATTRIBUTES: \n\n')
                        txt.write(str(attr) + '\n')
                        txt.write('\nEXIFTOOL DATA: \n\n')
                        e = subprocess.run(["exiftool %s" % (arg1)], shell=True, text=True, capture_output=True, universal_newlines=True)
                        txt.write(e.stdout)
                        txt.write("\nBINWALK DATA: \n\n")
                        b = subprocess.run(["binwalk %s" % (arg1)], shell=True, text=True, capture_output=True, universal_newlines=True)
                        txt.write(b.stdout)
                        txt.write("\nSTRINGS DATA: \n\n")

                        s = subprocess.run(["strings %s" % (arg1)], shell=True, text=True, capture_output=True, universal_newlines=True)
                        txt.write(s.stdout)




    def main(self):
        Security.welcome(self)
        signal.signal(signal.SIGINT, Security.signal_handler)
        print("Usage: ")
        print("python3 PhotoSec.py")
        print("Options: ")
        m_inp = input('''
        clear EXIF data (c), rename files (r), check for geo data (g), see usage/get help (g)
        ''').lower()
        if m_inp == "r":
            Security.rename_cli(self)
        elif m_inp == "c":
            Security.clear_cli(self)
        elif m_inp == "g":
            Security.check_geo(self)
        elif m_inp == "h" or m_inp == "help":
            Security.print_help(self)
        else:
            print("Please enter 'r' or 'c'")
            Security.main(self)


# if __name__ == '__main__':
#     Security("Start").main()

img = Security("Start")
img.image_analysis()
# im = open('/home/aes18/Pictures/test/puppy.jpg', 'rb')
# img = exif.Image(im)
# att = img.list_all()
# dtt = dir(img)
# print(att, "\n", dtt)
