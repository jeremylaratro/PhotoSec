import os

import exif
from exif import Image


# from exif import Image
# from PIL import Image
# from PIL.ExifTags import TAGS


def rename():
    directory = input("Enter the directory: ")
    name = input("Enter the prefix:")
    file_path = os.path.join(os.path.dirname(__file__), directory)
    for file in os.listdir(file_path):
        naming_prt = "s_" + file
        if file.endswith(".jpg"):
            os.rename(file_path+file, file_path+naming_prt)


def clear():
    directory = input("Enter the directory: ")
    file_path = os.path.join(os.path.dirname(__file__), directory)
    for file in os.listdir(file_path):
        if file.endswith(".jpg"):

            with open(file_path+file, 'br+') as f:

                img = exif.Image(f)
                if img.has_exif:
                    img.delete_all()
                    with open(file_path+file, 'wb') as mf:
                        mf.write(img.get_file())

                    os.rename(file_path+file, file_path+"scrubbed_"+file)
                else:
                    continue



print(clear())


