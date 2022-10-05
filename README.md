# PhotoCleaner
Python script which allows easy bulk scrubbing of photo EXIF data as well as renaming of files using python modules promoting online safety and opsec

## Usage
This script can be used as a CLI tool (interactive) or via CLI arguments and follow the prompts. \n
 - To use the CLI tool interactively, run the script without any arguments:
```bash
 python3 PhotoSec.py
```
 - To use the CLI tool with arguments:
 ```bash
 python3 PhotoSec.py 
          python3 PhotoSec.py -h / --help -r / --rename -c / --clear -g / --geo 
          
 ```         
>> Commands:
> -h or --help for help -r or --rename to rename files in a directory -c or --clear to bulk clear EXIF data from files in a directory -g or --geo to bulk check if images contain GPS/location data
 
Enter directory where photos are contained. 

Soon to be implemented:
  - Choose file names
  - edit specific EXIF parameters
  - file encryption
