# PhotoSecUtils
>Python script which allows easy bulk scrubbing of photo EXIF data as well as renaming of files using python modules promoting online safety and opsec
>
## Usage
>This script can be used as a CLI tool (interactive) or via CLI arguments and follow the prompts. \n
> - To use the CLI tool interactively, run the script without any arguments:
>```bash
> python3 photoutils.py
>```
> - To use the CLI tool with arguments:
> ```bash
> python3 photoutils.py -h / --help -r / --rename -c / --clear -g / --geo / -a / --analysis
>   
> ```     
>- It can also be run from outside of the directory as a module after using setup.py:
>```bash
>python3 setup.py build
>````
>```bash
>python3 setup.py install
>```
>```bash
>python3 -m PhotoSec
>```

  
>> Commands:
> 
> - -h or --help for help
> - -r or --rename to rename files in a directory 
> - -c or --clear to bulk clear EXIF data from files in a directory 
> - -g or --geo to bulk check if images contain GPS/location data
> - -a or --analysis to analyze and image file for information, malicious code injection, etc. 

## Requirements
>- This project was built using Python 3.10. It may work with other versions of Python 3, but this is not guaranteed.
>- This project has only been used and tested on Linux. 
>- Binwalk and exfitool must be installed on the system.

## Sources
> 
> This script makes use of various open-source programs and modules. Special thanks to Kenneth Leung for his work on the Exif module, as well as the creators of binwalk and exiftool. 

## Contributions
>
> Please feel free to offer comments, criticisms (constructive), or to contribute/add features/etc. I'm still in the early stages of my programming 'career' and am happy to take advice and ideas. 
 



