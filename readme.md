# MonkeyPack
A commandline packer and unpacker of Return To Monkey Island's ggpack files, written in Python 3.8.  
This project is based very much on the work done over at [Dinky Explorer](https://github.com/bgbennyboy/Dinky-Explorer). Thanks!

## Finding The Game Files
To find the game files in Steam: right-click 'Return To Monkey Island', select 'Manage', and then click 'Browse local files'. This opens a file explorer window in the location of the game files.

## Usage
This program can do three things: Unpack packed game files; pack files so that the game recognises them; list the contents of packed files.  
There are two ways to use MonkeyPack: drag & drop; and commandline.

### Drag & Drop
#### Unpacking
If you select one or more ggpack files in a file explorer, drag them over to MonkeyPack.exe (or main.py if you're using the Python scripts directly), and let go of the mouse button, MonkeyPack will unpack the provided ggpack file(s) in a subdirectory in the same place as MonkeyPack, named after the unpacked ggpack file(s).
#### Packing
If you select one or more non-ggpack files, drag them over to MonkeyPack.exe (or main.py if you're using the Python scripts directly), and let go of the mouse button, MonkeyPack will pack the provided file(s) into a new ggpack file, created in the same place as MonkeyPack.

If you place that newly created ggpack file in the 'Return To Monkey Island' folder (as found under 'Finding The Game Files'), the game will use the file(s) inside this new ggpack file instead of the original file(s), if the packed file(s) is/are named the same.

For instance: if you unpacked 'Weird.ggpack1a', you can get the 'Text_en.tsv' file from the unpacked files, and make a new translation. If you then drag and drop just this new 'Text_en.tsv' file onto MonkeyPack, a new ggpack file will be created, containing just this new translation. If you then put this newly created ggpack file inside the 'Return To Monkey Island' folder, the game should load your new translation as a replacement for the English text.

### Commandline
The basic format of the commandline calls depends on whether you're using the MonkeyPack executable or the Python script:  
**MonkeyPack.exe**:  monkeypack.exe [subcommand] [file1] (file2)...  
**Python**: python main.py [subcommand] [file1] (file2)...  
**Python (MacOS)**: python3 main.py [subcommand] [file1] (file2)...  
In the following examples, you can substitute 'monkeypack.exe' with 'python main.py' (or 'python3 main.py' on MacOS), and it should work the same.  
Files can be specified by absolute or relative path.

Available subcommands:
#### Subcommand 'help'
Shows a short explanation on how to use MonkeyPack.

#### Subcommand 'list'
Shows a list of the files inside the provided ggpack file(s), and writes the same list to a file named after the ggpack file followed by '.txt'.  
Example: 'monkeypack.exe list "C:\Program Files (x86)\Steam\steamapps\common\Return To Monkey Island\Weird.ggpack1a"' will show all files inside 'Weird.ggpack1a' in the command prompt window, and will create a file next to monkeypack.exe called 'Weird.ggpack1a.txt' with the same info as shown in the command prompt.  

#### Subcommand 'unpack'
Unpacks the provided ggpack file(s) into a subdirectory in the same place as MonkeyPack, named after the unpacked ggpack file(s).  
Example: 'monkeypack.exe unpack "C:\Program Files (x86)\Steam\steamapps\common\Return To Monkey Island\Weird.ggpack4a"' will create a new directory in the same place where MonkeyPack.exe exists called 'Weirdggpack4a', with all the files inside the 'Weird.ggpack4a' file.  

#### Subcommand 'pack'
Packs the provided file(s) into a single new ggpack file, placed in the same place as MonkeyPack. This file will end with a number and letter not used by the game, ready to be placed in the same folder as 'Return To Monkey Island'.  
The first file will be named 'Weird.ggpack6', the next 'Weird.ggpack6a', and so on. The highest number that the game reads is 9, and the highest letter is 'f'. So the highest ggpack file the game still recognises is 'Weird.ggpack9f', after that MonkeyPack won't create new ggpack files anymore.
Example: 'monkeypack.exe pack Text_en.tsv' will create a new ggpack file in the same place as MonkeyPack containing the file 'Text_en.tsv' (which should exist in the same location as MonkeyPack for this example).
You can also provide a folder, in which case all the files inside that folder will be added to the newly created ggpack file too. This does *not* work recursively, so folders inside the provided folder will be ignored.

#### Filtering the result
You can also add filename filters. Use '?' to match a single character ('Text_??.txt'), and '\*' to match multiple characters ('\*.txt').  
For 'list' and 'unpack', adding filename filters only lists or unpacks files that match the filter.  
For 'pack', adding filename filters only packs files into the new ggpack file that match the filter.
Example: 'monkeypack.exe unpack "C:\Program Files (x86)\Steam\steamapps\common\Return To Monkey Island\Weird.ggpack1a" \*.tsv' only unpacks files that end with '*.tsv'

## Version History

### Version 0.3 - 2022-10-17
- Fix a bug in the GGDict parser, that could make it miss some strings in the strings list

### Version 0.2 - 2022-10-10:
- Don't keep all the files to pack in memory. This massively reduces memory usage during packing
- 'pack' now ignores ggpack files
- Add filename filtering. For example, 'monkeypack.exe unpack path/to/game/Weird.ggpack1a *.tsv' only unpacks the .tsv files from the ggpack file. Works for 'list' and 'pack' too.
- Update help inside program
- Update and expand readme

### Version 0.1 - 2022-10-03:
- Initial release 
