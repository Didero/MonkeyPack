import hashlib, struct

def _parseFromFormatString(dataToParse: bytes, formatString: str):
	return struct.unpack(formatString, dataToParse)[0]

def parseInt(dataToParse: bytes, startIndex: int = 0) -> int:
	return _parseFromFormatString(dataToParse[startIndex: startIndex + 4], '<i')

def readInt(f) -> int:
	return parseInt(f.read(4))

def parseShort(dataToParse: bytes, startIndex: int = 0) -> int:
	return _parseFromFormatString(dataToParse[startIndex: startIndex + 2], '<h')

def readShort(f) -> int:
	return parseShort(f.read(2))

def readString(data: bytes, startIndex: int) -> str:
	terminatedIndex = data.find(b'\x00', startIndex)
	stringAsBytes = data[startIndex: terminatedIndex]
	try:
		return stringAsBytes.decode('utf-8')
	except UnicodeDecodeError as e:
		print(f"Unable to convert {getPrintableBytes(stringAsBytes)} ({stringAsBytes}) to a string, {startIndex=}")
		raise e


def toWritableInt(numberToWrite: int) -> bytes:
	return struct.pack('<i', numberToWrite)

def toWritableShort(numberToWrite: int) -> bytes:
	return struct.pack('<h', numberToWrite)

def toStringInt(i: int) -> str:
	"""The file index uses a null-terminated string representation of a number for the offset and size. This method creates such a string from the provided number"""
	return str(i) + '\x00'

def getPrintableBytes(b: bytes) -> str:
	return b.hex(' ', 1)

def calculateMd5Hash(b: bytes) -> str:
	return hashlib.md5(b).hexdigest()
