import argparse
import os
import exif

class Security:
    def __init__(self, name):
        self.name = name

    @staticmethod
    def get_dir():
        print("Make sure that directory ends with '/'")
        directory = input("Enter the directory: ")
        file_path = os.path.join(os.path.dirname(__file__), directory)
        return file_path

    def get_photos(self):
        file_path = self.get_dir()
        photos = ['.jpg', '.jpeg', '.png', '.gif']
        for file in os.listdir(file_path):
            if file.endswith(tuple(photos)):
                return file_path, file
        print("No photos found in the specified directory.")
        exit()

    @staticmethod
    def signal_handler(sig, frame):
        choice = input("Are you sure you want to exit? (y/n): ")
        if choice.lower() == 'y':
            sys.exit(0)

    def continue_q(self):
        print("Would you like to continue? (y/n): ")
        choice = input().lower()
        if choice == 'y':
            self.main()
        else:
            exit()

    def print_help(self):
        print("Usage: ")
        print(''' 
        This script can be used as a CLI tool (interactive) or via CLI arguments and follow the prompts.
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
               - Ensure that a '/' is at the end of the directory path
               - Ensure that the file extension is correct. Currently, the file must contain an extension, i.e., 'file' 
               will not work, but file.jpg' will. 
        ''')
        self.main()

    def clear_cli(self):
        cl = 0
        file_path, file = self.get_photos()
        for file in os.listdir(file_path):
            with open(os.path.join(file_path, file), 'br+') as f:
                img = exif.Image(f)
                att = img.list_all()
                if '_gps_ifd_pointer' in att:
                    cl += 1
                    del img.gps_latitude
                    del img.gps_longitude
                    f.seek(0)
                    f.write(img.get_file())
                    f.truncate()
                else:
                    continue
        print(f"EXIF data cleared from {cl} files!")
        self.continue_q()

    def check_geo(self):
        gps_data_t = {}
        gps_data_l = []
        i = 0
        file_path, file = self.get_photos()
        for file in os.listdir(file_path):
            with open(os.path.join(file_path, file), 'rb+') as f:
                img = exif.Image(f)
                att = img.list_all()
                if '_gps_ifd_pointer' in att:
                    print("GPS data found in file: " + file)
                    gps_data_l.append(f'File {i}: ' + file)
                    gps_data_l.append('LAT/LONG:')
                    gps_data_l.append(img.gps_latitude + img.gps_longitude)
                    gps_data_t[file] = {'LAT': img.gps_latitude, 'LONG': img.gps_longitude}
                    i += 1
                else:
                    print("No GPS data found in file: " + file)
        self.continue_q()
        print(gps_data_l)

    def image_analysis(self):
        print("This feature analyzes an image using exiftool, binwalk, strings,"
              " and the exif module, and outputs the results to a text file for analysis."
              "This features currently only works for single images at a time. ")
        i = 0
        file_path, file = self.get_photos()
        for file in os.listdir(file_path):
            with open(os.path.join(file_path, file), 'br+') as f:
                img = exif.Image(f)
                with open(os.path.join(os.getcwd(), 'ExifData', file + '_analysis_.txt'), 'w+') as txt:
                    txt.write('Image Analysis: \n')
                    txt.write(f'File path: {os.path.join(file_path, file)}\n')
                    txt.write(f'Image attributes: {img.list_all()}\n')
        print("Image analysis completed.")
