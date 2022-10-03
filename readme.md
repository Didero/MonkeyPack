## MonkeyPack
A commandline packer and unpacker of Return To Monkey Island's ggpack files, written in Python 3.

### Usage
You can drag your file(s) on top of this program. If they're ggpack files, they'll be unpacked. Otherwise, a new ggpack file will be created with those files inside it.  
You can also provide the filename(s) on the command line, that works the same way as dragging them onto the program.  
Packed and unpacked files are always written in the folder where this program is, so make sure you have write permission.  
There are also commandline options if you want more control, that should be typed after the program name, without preceding dashes:
* **help**: Print this help.  
* **list** \[path to ggpack file\]: Lists which files are inside the provided ggpack file, and also writes that info to a textfile named after the ggpack file.  
* **unpack** \[path to ggpack file\]: Unpacks the provided ggpack file in the current directory, inside a folder named after the ggpack file. Multiple ggpack files can be provided, separated by a space.
    The files are unpacked as they are, so no further decoding of for instance the music soundbank or script files is done.  
* **pack** \[list of files/folders to pack\]: Packs the provided files (separated by spaces) into a single ggpack file, that will be placed in the current directory.
    If a folder name is provided, all the files inside that folder will be packed, but subfolders are ignored.
    The newly created ggpack file will be called 'Weird.ggpack' followed by the highest number-letter combination available. The number can be 1-9, and the letter a-f.
    So after 'Weird.ggpack9f' has been created, no higher number-letter suffix will be picked up by the game. MonkeyPack will show an error if no more valid ggpack's can be created


This is based very much on the work done over at [Thimbleweed Park Explorer](https://github.com/bgbennyboy/Thimbleweed-Park-Explorer). Thanks!