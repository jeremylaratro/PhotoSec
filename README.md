# PhotoSecUtils
Python script which allows easy bulk scrubbing of photo EXIF data as well as renaming of files using python modules promoting online safety and opsec

## Usage
This script can be used as a CLI tool (interactive) or via CLI arguments and follow the prompts. \n
 - To use the CLI tool interactively, run the script without any arguments:
```bash
 python3 PhotoSec.py
```
 - To use the CLI tool with arguments:
 ```bash
 python3 PhotoSec.py -h / --help -r / --rename -c / --clear -g / --geo / -a / --analysis
   
 ```         
>> Commands:
> 
> - -h or --help for help
> - -r or --rename to rename files in a directory 
> - -c or --clear to bulk clear EXIF data from files in a directory 
> - -g or --geo to bulk check if images contain GPS/location data
> - -a or --analysis to analyze and image file for information, malicious code injection, etc. 

>> Contributions
>
> Please feel free to offer comments, criticisms (constructive), or to contribute/add features/etc. I'm still in the early stages of my programming 'career' and am happy to take advice and ideas. 
 



