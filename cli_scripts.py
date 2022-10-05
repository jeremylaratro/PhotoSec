# import exif
# import os
#
# def welcome():
#     print("Welcome to the CLI photo scrubber!")
#     print("This program will remove all EXIF data from photos in a directory.")
#     print("You can also rename the files in the directory.")
#     print("Please note that this program will overwrite the original files.")
#     print("Please make sure you have a backup of the files before running this program.")
#     print("")
#
# def get_dir():
#     directory = input("Enter the directory: ")
#     return directory
# def rename_cli():
#     directory = Security.get_dir(self)
#     # prompt user to enter directory where files are stored
#     # directory = input("Enter the directory: ")
#     name = input("Enter the file name you'd like to use (ie: RL0, RL1, RL2, etc): ")
#     file_path = os.path.join(os.path.dirname(__file__), directory)
#     # number each file in the directory starting with 1
#     i = 1
#     # loop through each file in the directory
#     for file in os.listdir(file_path):
#         # get the file extension
#         ext = os.path.splitext(file)[-1]
#         print(ext)
#         # rename the file
#         os.rename(os.path.join(file_path, file), os.path.join(file_path, name + str(i)) + ext)
#         # increment i by 1
#         i += 1
#     #debug
#     print(file_path)
#
#
#
# # len(os.listdir(file_path)
# def clear_cli():
#     directory = Security.get_dir(self)
#     # directory = input("Enter the directory where photos are stored: ")
#     rename = input("Would you like to rename the files? (y/n): ")
#     file_path = os.path.join(os.path.dirname(__file__), directory)
#     photos = [".jpg", ".jpeg", ".png", ".gif"]
#     for file in os.listdir(file_path):
#         if file.endswith(tuple(photos)):
#             with open(file_path + file, 'br+') as f:
#                 img = exif.Image(f)
#                 if img.has_exif:
#                     img.delete_all()
#                     with open(file_path + file, 'wb') as mf:
#                         mf.write(img.get_file())
#                     if rename == "y":
#                         Security.rename_cli(self)
#                     # os.rename(file_path+file, file_path+"scrubbed_"+file)
#                 else:
#                     continue
#
#
# #
# # print(clear())
# imp1 = Security('test')
#
#
# # imp1.rename_cli()
# imp1.clear_cli()
#
