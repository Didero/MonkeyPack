import datetime, os, sys, time
from typing import Dict, List, Tuple

import Keys, Utils
from CustomExceptions import DecodeError
from GGDict import GGDict

# The current folder depends on whether this is run as a Python script or as a PyInstaller-created executable
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
	# Running in a PyInstaller bundle
	CURRENT_FOLDER = os.path.abspath(os.path.dirname(sys.executable))
else:
	# Running in a normal Python process
	CURRENT_FOLDER = os.path.abspath(os.path.dirname(__file__))


def decodeGameData(encodedGameData: bytes) -> bytes:
	"""Decodes the provided encoded game data into something parseable, or turns decoded data back into encoded data"""
	# From https://github.com/bgbennyboy/Thimbleweed-Park-Explorer/blob/master/ThimbleweedLibrary/BundleReader_ggpack.cs#L627
	encodedGameDataLength = len(encodedGameData)
	decodedByteArray = bytearray(encodedGameDataLength)
	decodeSum = ((len(encodedGameData)) + Keys.MAGIC_VALUE) & 0xFFFF
	for index in range(encodedGameDataLength):
		key1decodeByte = Keys.KEY_1[(decodeSum + Keys.MAGIC_VALUE) & 0xFF]
		key2decodeByte = Keys.KEY_2[decodeSum]
		decodedByteArray[index] = (encodedGameData[index] ^ key1decodeByte ^ key2decodeByte)
		decodeSum = (decodeSum + Keys.KEY_1[decodeSum & 0xFF]) & 0xFFFF
	return bytes(decodedByteArray)


def listFiles(packFilepath: str):
	"""List all the files inside the specified ggpack file"""
	if not os.path.isfile(packFilepath):
		raise FileNotFoundError(f"Asked to list files inside '{packFilepath}' but that file doesn't exist")
	fileIndex = parseFileIndex(packFilepath)
	# Write the found files to the screen and to a textfile too, to make it easier to look through when there's a lot of files
	outputFilepath = os.path.join(CURRENT_FOLDER, os.path.basename(packFilepath) + '.txt')
	with open(outputFilepath, 'w') as outputFile:
		printAndWrite(f"Found {len(fileIndex['files']):,} files inside '{packFilepath}':", outputFile)
		for fileCount, fileEntry in enumerate(fileIndex['files']):
			printAndWrite(f"File {fileCount + 1:,} of {len(fileIndex['files']):,}: '{fileEntry['filename']}', {fileEntry['size']:,} bytes", outputFile)
	print(f"Listed {len(fileIndex['files']):,} files inside {packFilepath}, this list has also been written to '{outputFilepath}'")

def unpack(unpackFilePath: str):
	"""Unpacks the provided ggpack file into a folder named after the provided ggpack file"""
	if not os.path.isfile(unpackFilePath):
		raise FileNotFoundError(f"Asked to unpack file '{unpackFilePath}', but that file doesn't exist")
	# Dump the files inside a folder named after the pack file. That folder will be created where this script is
	extractFolder = os.path.join(CURRENT_FOLDER, os.path.basename(unpackFilePath).replace('.', ''))
	fileIndex = parseFileIndex(unpackFilePath)
	os.makedirs(extractFolder, exist_ok=True)
	totalFileCount = len(fileIndex['files'])
	for fileCount, fileEntry in enumerate(fileIndex['files']):
		if len(fileEntry) < 3:
			print(f"Skipping unpacking '{fileEntry}' from '{fileIndex}', not enough info stored")
			continue
		if 'filename' not in fileEntry or 'offset' not in fileEntry or 'size' not in fileEntry:
			print(f"Invalid file entry '{fileEntry}', missing key 'filename', 'offset', or 'size', skipping")
			continue
		print(f"Unpacking file {fileCount + 1:,} of {totalFileCount:,}: '{fileEntry['filename']}', {fileEntry['size']:,} bytes")
		encodedFileData = getEncodedPackFile(unpackFilePath, fileEntry['offset'], fileEntry['size'])
		if '.bank' in fileEntry['filename']:
			# .bank files aren't encoded
			decodedFileData = encodedFileData
		else:
			decodedFileData = decodeGameData(encodedFileData)
		filePath = os.path.join(extractFolder, fileEntry['filename'])
		with open(filePath, 'wb') as f:
			f.write(decodedFileData)
	print(f"Successfully unpacked {totalFileCount:,} files from '{unpackFilePath}' into '{extractFolder}")

def parseFileIndex(gameFilePath: str) -> Dict:
	encodedFileIndex = getEncodedFileIndex(gameFilePath)
	decodedFileIndex = decodeGameData(encodedFileIndex)
	gameFileIndex = GGDict.fromGgDict(decodedFileIndex, True)
	return gameFileIndex

def getEncodedFileIndex(gameFilePath: str) -> bytes:
	print(f"Opening game file '{gameFilePath}'")
	with open(gameFilePath, 'rb') as gameFile:
		fileSize = os.path.getsize(gameFilePath)
		if fileSize < 12:
			raise DecodeError(f"File '{gameFilePath}' is too small to be a ggpack file")
		dataOffset = Utils.readInt(gameFile)
		dataSize = Utils.readInt(gameFile)
		if dataSize < 1:
			raise DecodeError(f"Invalid data size of {dataSize}")
		if dataOffset + dataSize > fileSize:
			raise DecodeError(f"Found an offset of {dataOffset:,} and a data size of {dataSize:,}, totalling {dataOffset + dataSize:,}, but the file is only {fileSize:,} bytes on disk")
		gameFile.seek(dataOffset)
		return gameFile.read(dataSize)

def getEncodedPackFile(gameFilePath: str, startOffset: int, size: int = None):
	with open(gameFilePath, 'rb') as gameFile:
		gameFile.seek(startOffset)
		if size:
			return gameFile.read(size)
		else:
			raise DecodeError(f"Missing size parameter for entry at start offset {startOffset}")


def packFiles(filenamesToPack: List[str]):
	"""Pack the files from the provided filenames into a ggpack that the game can recognise"""
	# First determine which ggpack filename we can use.
	packFilename = getAvailableFilename()
	if not packFilename:
		raise FileExistsError(f"There are already too many Weird.ggpack files in this folder, valid ggpacks end with 1-9 and optionally the letters a to f")
	fileOffsetsDict = {"files": [], "guid": "b554baf88ff004c50cc0214575794b8c"}  # All the RtMI ggpack files use the same guid, use it for our packfile too
	with open(packFilename, 'wb') as packFile:
		# First write two dummy integers, these will get overwritten later with the file index start offset and the file index size, once we know those
		packFile.write(Utils.toWritableInt(0))
		packFile.write(Utils.toWritableInt(0))
		# Write the files to the pack file
		for fileCount, filenameToPack in enumerate(filenamesToPack):
			# If a directory was specified, pack all the files inside it
			if os.path.isdir(filenameToPack):
				for fn in os.listdir(filenameToPack):
					filenameInFolder = os.path.join(filenameToPack, fn)
					if not os.path.isdir(filenameInFolder):
						filenamesToPack.append(filenameInFolder)
				continue
			if not os.path.isfile(filenameToPack):
				raise FileNotFoundError(f"Asked to pack file '{filenameToPack}' but that file doesn't exist")
			if 'ggpack' in os.path.splitext(filenameToPack)[1].lower():
				print(f"Skipping packing of ggpack file '{filenameToPack}'")
				continue
			print(f"Packing file {fileCount + 1:,} of {len(filenamesToPack):,}: '{filenameToPack}'")
			with open(filenameToPack, 'rb') as fileToPack:
				# .bank files contain music and sounds, and are stored unencoded
				if filenameToPack.endswith('.bank'):
					encodedDataToPack = fileToPack.read()
				else:
					encodedDataToPack = decodeGameData(fileToPack.read())
				fileOffsetsDict['files'].append({"filename": os.path.basename(filenameToPack), "offset": packFile.tell(), "size": len(encodedDataToPack)})
				packFile.write(encodedDataToPack)
		# Then add the file index
		print(f"Writing file index '{packFilename}'")
		fileIndexStartOffset = packFile.tell()
		fileIndex = GGDict.toGgDict(fileOffsetsDict, True)
		packFile.write(decodeGameData(fileIndex))
		# Now we can overwrite the initial two ints, the file index start offset and size
		packFile.seek(0)
		packFile.write(Utils.toWritableInt(fileIndexStartOffset))
		packFile.write(Utils.toWritableInt(len(fileIndex)))
	print(f"Successfully packed {len(filenamesToPack):,} files into '{packFilename}'")

def getAvailableFilename():
	# Valid extensions after the 'ggpack' part are 1 to 9, optionally followed by the letter a to f
	for i in range(6, 10):
		letterlessFilename = os.path.join(CURRENT_FOLDER, f'Weird.ggpack{i}')
		if not os.path.isfile(letterlessFilename):
			return letterlessFilename
		for letter in 'abcdef':
			letteredFilename = letterlessFilename + letter
			if not os.path.isfile(letteredFilename):
				return letteredFilename
	return None

def printAndWrite(stringToWrite: str, fileToWriteTo):
	print(stringToWrite)
	fileToWriteTo.write(stringToWrite + '\n')

def parseFileArguments(argumentList: List[str]) -> Tuple[List[str], List[str]]:
	"""
	Split the provided filename arguments into two separate filename lists
	:param argumentList: The list of filenames to parse
	:return: A tuple with two lists: One with ggpack filenames, one with normal filenames
	"""
	packList: List[str] = []
	filenameList: List[str] = []
	for fn in argumentList:
		if '.ggpack' in fn:
			packList.append(fn)
		else:
			filenameList.append(fn)
	return packList, filenameList

def printHelp():
	print("MonkeyPack is a simple tool to unpack and pack files from the game Return To Monkey Island")
	print("You can drag your file(s) on top of this program. If they're ggpack files, they'll be unpacked. Otherwise, a new ggpack file will be created with those files inside it.")
	print("You can also provide the filename(s) on the command line, that works the same way as dragging them onto the program.")
	print("Packed and unpacked files are always written in the folder where this program is, so make sure you have write permission.")
	print("There are also command line options if you want more control, that should be typed after the program name, without preceding dashes:")
	print("  help: Print this help")
	print("  list [list of ggpack files]: List which files are inside the provided ggpack files, and also writes that info to textfiles named after the ggpack files.")
	print("  unpack [list of ggpack files]: Unpacks the provided ggpack files in the current directory, each inside a folder named after that ggpack file.")
	print("  pack [list of files/folders to pack]: Packs the provided files (separated by spaces) into a single ggpack file, that will be placed in the current directory. If a folder name is provided, all the files inside that folder will be packed, but subfolders are ignored.")
	print("See the included readme or https://github.com/didero/monkeypack for a more elaborate usage guide")

def main():
	startTime = time.perf_counter()
	try:
		if len(sys.argv) < 2:
			printHelp()
			return
		command = sys.argv[1].lower().lstrip('-')
		argumentList = sys.argv[2:]
		if command == 'help':
			printHelp()
			return

		if command not in ('list', 'pack', 'unpack'):
			# Try to guess what to do with the provided argument(s)
			print("WARNING: No explicit command provided, guessing what to do. Call this script with 'help' to see the availble commands")
			if not os.path.exists(sys.argv[1]):
				print(f"ERROR: Unknown command '{sys.argv[1]}'")
				printHelp()
				return
			if '.ggpack' in sys.argv[1]:
				command = 'unpack'
			else:
				command = 'pack'
			# The first argument was apparently a file, add it back into the argument list
			argumentList.insert(0, sys.argv[1])

		packFilenameList, filenameList = parseFileArguments(argumentList)
		if len(packFilenameList) == 0 and len(filenameList) == 0:
			print("ERROR: No filenames provided")
			printHelp()
			return

		if command == 'list':
			if len(packFilenameList) == 0:
				print("ERROR: Please add one or more ggpack files to list the contents of")
			else:
				if len(filenameList) > 0:
					print("WARNING: Some of the provided filenames aren't ggpack files, they will be ignored")
				for packFilename in packFilenameList:
					listFiles(packFilename)
		elif command == 'unpack':
			if len(packFilenameList) == 0:
				print("ERROR: Please add one or more ggpack files to unpack")
			else:
				if len(filenameList) > 0:
					print("WARNING: Some of the provided filenames aren't ggpack files, they will be ignored")
				for packFilename in packFilenameList:
					unpack(packFilename)
		elif command == 'pack':
			if len(filenameList) == 0:
				print("ERROR: Please add one or more files to pack into a ggpack file")
			else:
				if len(packFilenameList) > 0:
					print("WARNING: Some of the provided files are ggpack files, they can't be packed so they will be ignored")
				packFiles(filenameList)
		else:
			print(f"ERROR: Unknown command '{command}'")
			printHelp()
	except Exception as e:
		print(f"ERROR: {e}")
		with open('error.log', 'a') as errorFile:
			errorFile.write(f"[{datetime.datetime.now()}] {e}")
			errorFile.write('\n')
	finally:
		print(f"Execution finished in {time.perf_counter() - startTime:.6f} seconds")


if __name__ == '__main__':
	main()
