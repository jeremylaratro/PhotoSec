import argparse
from PhotoSec import PhotoSec, Security


def start():
    print('''
    
    --------------------- Welcome to the CLI PhotoSec utils! -------------------------------------------------
    //         .---.         `_______```__``````````````````__````````````````______``````````````````````   //
   //          |[X]|         |```````\`|``\````````````````|``\``````````````/``````\```````````````````````// 
   //   _.==._.""""".___~__  |`$$$$$$$\|`$$____````______`_|`$$_````______``|``$$$$$$\``______````_______``//
   //  d __ ___.-''-. _____b |`$$__/`$$|`$$````\``/``````\```$$`\``/``````\`|`$$___\$$`/``````\``/```````\ //
   //  |[__]  /."__".\ _   | |`$$````$$|`$$$$$$$\|``$$$$$$\$$$$$$`|``$$$$$$\`\$$````\`|``$$$$$$\|``$$$$$$$ //
   //  |     /  /""\  \ (_)| |`$$$$$$$`|`$$``|`$$|`$$``|`$$|`$$`__|`$$``|`$$`_\$$$$$$\|`$$````$$|`$$`````` //
   //  |     \  \__/  /    | |`$$``````|`$$``|`$$|`$$__/`$$|`$$|``\`$$__/`$$|``\__|`$$|`$$$$$$$$|`$$_____` //
   //  |      \`.__.'/     | |`$$``````|`$$``|`$$`\$$````$$`\$$``$$\$$````$$`\$$````$$`\$$`````\`\$$`````\ //
   //  \=======`-..-'======/ `\$$```````\$$```\$$``\$$$$$$```\$$$$``\$$$$$$```\$$$$$$```\$$$$$$$``\$$$$$$$ // 
  //    `-----------------'  `````````````````````````````````````````````````````````````````````````````//
      
   --------------------------------------------------------------------------------- V0.2.0 -------------
    
    [+] This script contains functions to bulk clear EXIF data, check for GPS data, 
        rename files and perform image analysis with popular tools into a single output. 
    [+] Please note that this program will overwrite the original files. 
        Make sure you have a backup of the files before running this program
    [+] if you wish to preserve this data; author not responsible for any data loss.
    [+] Author: Jeremy Laratro
    [+] github.com/jeremylaratro

    
                     ''')

    parser = argparse.ArgumentParser()
    if parser is not None:
        parser.add_argument("-a", "--analysis", help="Analyze a photo using other open-source tools and output the "
                                                     "results to a text file for analysis", action="store_true")
        parser.add_argument("-r", "--rename", help="Rename files in a directory", action="store_true")
        parser.add_argument("-c", "--clear", help="Clear EXIF data from files in a directory", action="store_true")
        parser.add_argument("-g", "--geo", help="Bulk check if images contain GPS/location data", action="store_true")
        args = parser.parse_args()
        p = Security('PhotoSec')
        if args.rename:
            p.rename_cli()
        elif args.clear:
            p.clear_cli()
        elif args.geo:
            p.check_geo()
        elif args.analysis:
            p.image_analysis()
        else:
            p.main()
        # elif args.help or not args.rename or not args.clear:
        #     p.print_help()
    else:

        main_start = Security('PhotoSec')
        main_start.main()


if __name__ == '__main__':
    start()
