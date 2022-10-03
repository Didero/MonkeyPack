from enum import Enum
from io import BytesIO
from typing import Any, Dict, List

import Utils
from CustomExceptions import DecodeError, GGDictError


class _ValueType(Enum):
	DICT = b'\x02'
	ARRAY = b'\x03'
	STRING = b'\x04'
	INTEGER = b'\x05'

class GGDict:
	"""
	Thimbleweed Park, Delores, and Return To Monkey Island store some data in a specialised format called a GGDict
	This class can read, parse, and write them
	"""

	DECODED_HEADER = b'\x01\x02\x03\x04'
	VERSION_HEADER = b'\x01\x00\x00\x00'
	FILE_INDEX_END = b'\xFF\xFF\xFF\xFF'
	STRING_OFFSETS_START = b'\x07'
	STRINGS_START = b'\x08'

	@staticmethod
	def fromGgDict(sourceData: bytes, useShortStringIndex: bool):
		"""
		This class parses the provided data into a GGDict, if it's valid
		:param sourceData: The data to parse into a GGDict
		:param useShortStringIndex: Whether to use 2 bytes or 4 bytes to read string indexes. Thimbleweed Park and Delores use 4 bytes ('False'), Return To Monkey Island uses 2 bytes ('True')
		:return: The parsed structure, usually a dictionary
		"""
		# Verify the header to see if the source data is parsable
		if sourceData[0:4] != GGDict.DECODED_HEADER or sourceData[4:8] != GGDict.VERSION_HEADER:
			raise DecodeError(f"Invalid header. Should be '{Utils.getPrintableBytes(GGDict.DECODED_HEADER)} {Utils.getPrintableBytes(GGDict.VERSION_HEADER)}, but is {Utils.getPrintableBytes(sourceData[0:8])}")
		sourceDataLength = len(sourceData)
		# Get the start offset of the file index entries
		offsetsListStart = Utils.parseInt(sourceData, 8) + 1
		if offsetsListStart >= sourceDataLength:
			raise DecodeError(f"String offsets supposedly start at offset {offsetsListStart:,} but there are only {sourceDataLength:,} bytes available")
		elif offsetsListStart < 12:
			raise DecodeError(f"Invalid index start offset of {offsetsListStart:,}, too small")
		# Iterate over the offsets and retrieve the string at each location
		stringList: List[str] = []
		for currentOffsetsListOffset in range(offsetsListStart, sourceDataLength - offsetsListStart, 4):
			stringOffset = Utils.parseInt(sourceData, currentOffsetsListOffset)
			if stringOffset <= -1:
				# '-1' signals the end of the offsets list, so we can stop
				break
			stringList.append(Utils.readString(sourceData, stringOffset))
		# The section after the offsetsListStart explains how the strings are organised
		sourceDataAsIo = BytesIO(sourceData)
		sourceDataAsIo.seek(12)
		return GGDict._readValue(sourceDataAsIo, stringList, useShortStringIndex)

	@staticmethod
	def _readValue(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool):
		valueType = sourceData.read(1)
		if valueType == _ValueType.DICT.value:
			return GGDict._readDictionary(sourceData, stringList, useShortStringIndex)
		elif valueType == _ValueType.ARRAY.value:
			return GGDict._readArray(sourceData, stringList, useShortStringIndex)
		elif valueType == _ValueType.STRING.value:
			return GGDict._readString(sourceData, stringList, useShortStringIndex)
		elif valueType == _ValueType.INTEGER.value:
			return GGDict._readInteger(sourceData, stringList, useShortStringIndex)
		else:
			raise GGDictError(f"Encountered unknown value type {valueType}")

	@staticmethod
	def _readDictionary(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> Dict[str, Any]:
		result = {}
		itemCount = Utils.readInt(sourceData)
		for itemIndex in range(itemCount):
			keyName = GGDict._readString(sourceData, stringList, useShortStringIndex)
			value = GGDict._readValue(sourceData, stringList, useShortStringIndex)
			if keyName in result:
				print(f"Duplicate key '{keyName}', old value is {result[keyName]}, overwriting with {value}")
			result[keyName] = value
		GGDict._verifyBlockIsClosed(sourceData, _ValueType.DICT)
		return result

	@staticmethod
	def _readArray(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> List[Any]:
		itemCount = Utils.readInt(sourceData)
		result = []
		for itemIndex in range(itemCount):
			result.append(GGDict._readValue(sourceData, stringList, useShortStringIndex))
		# An array also ends with the array marker
		GGDict._verifyBlockIsClosed(sourceData, _ValueType.ARRAY)
		return result

	@staticmethod
	def _readString(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> str:
		stringIndex = Utils.readShort(sourceData) if useShortStringIndex else Utils.readInt(sourceData)
		if stringIndex < 0 or stringIndex >= len(stringList):
			raise GGDictError(f"Invalid string index {stringIndex}, string list contains {len(stringList):,} strings. StringList is {stringList}")
		return stringList[stringIndex]

	@staticmethod
	def _readInteger(sourceData: BytesIO, stringList: List[str], useShortStringIndex: bool) -> int:
		return int(GGDict._readString(sourceData, stringList, useShortStringIndex), 10)

	@staticmethod
	def _verifyBlockIsClosed(sourceData, valueTypeToClose: _ValueType):
		closeByte = sourceData.read(1)
		if closeByte != valueTypeToClose.value:
			raise GGDictError(f"ValueType wasn't closed properly. Expected {valueTypeToClose.value} but was {closeByte} (At position {sourceData.tell():,})")

	@staticmethod
	def toGgDict(valueToConvert, useShortStringIndex: bool) -> bytes:
		"""
		Convert the provided value into a GGDict structure that Thimbleweed Park, Delores, and Return To Monkey Island can understand
		:param valueToConvert: The value to convert. Should usually be a dictionary
		:param useShortStringIndex: Whether to use 2 bytes or 4 bytes to read string indexes. Thimbleweed Park and Delores use 4 bytes ('False'), Return To Monkey Island uses 2 bytes ('True')
		:return: The GGDict structure
		"""
		# Create the dict structure itself first. Later we'll add the offsets and the stringlist, but we need this size to be able to calculate offsets
		stringList: List[str] = []
		ggdictOutput = bytearray()
		GGDict._writeValue(ggdictOutput, stringList, useShortStringIndex, valueToConvert)
		# Now we can create the string offsets and strings (The +4 is for the int indicating the offset where the string offsets list starts)
		stringIndexOffset = len(GGDict.DECODED_HEADER) + len(GGDict.VERSION_HEADER) + 4 + len(ggdictOutput)
		output = bytearray()
		output.extend(GGDict.DECODED_HEADER)
		output.extend(GGDict.VERSION_HEADER)
		output.extend(Utils.toWritableInt(stringIndexOffset))
		output.extend(ggdictOutput)
		# Now we can start writing the string list
		stringListOutput = bytearray()
		stringListOffsets: List[int] = []
		for s in stringList:
			stringListOffsets.append(len(stringListOutput))
			stringListOutput.extend(bytes(s, encoding='utf-8'))
			stringListOutput.extend(b'\x00')  # Strings are 0-terminated
		# The string offsets should be from the start of the ggdict, so add the ints (4 bytes) we're going to write for each string offset, plus the block closing and opening indicators
		baseStringOffset = stringIndexOffset + len(stringList) * 4 + len(GGDict.FILE_INDEX_END) + len(GGDict.STRING_OFFSETS_START) + len(GGDict.STRINGS_START)
		output.extend(GGDict.STRING_OFFSETS_START)
		for stringListOffset in stringListOffsets:
			output.extend(Utils.toWritableInt(baseStringOffset + stringListOffset))
		output.extend(GGDict.FILE_INDEX_END)
		output.extend(GGDict.STRINGS_START)
		output.extend(stringListOutput)
		return bytes(output)

	@staticmethod
	def _writeValue(output: bytearray, stringList: List[str], useShortStringIndex: bool, value: Any):
		if isinstance(value, dict):
			GGDict._writeDictionary(output, stringList, useShortStringIndex, value)
		elif isinstance(value, list):
			GGDict._writeArray(output, stringList, useShortStringIndex, value)
		elif isinstance(value, str):
			GGDict._writeString(output, stringList, useShortStringIndex, value)
		elif isinstance(value, int):
			GGDict._writeInteger(output, stringList, useShortStringIndex, value)
		else:
			raise GGDictError(f"Writing value type '{type(value)}' hasn't been implemented yet ({value=})")

	@staticmethod
	def _writeDictionary(output: bytearray, stringList: List[str], useShortStringIndex: bool, d: Dict[str, Any]):
		output.extend(_ValueType.DICT.value)
		output.extend(Utils.toWritableInt(len(d)))
		for key in d:
			GGDict._writeString(output, stringList, useShortStringIndex, key, False)
			GGDict._writeValue(output, stringList, useShortStringIndex, d[key])
		# Close off the dict
		output.extend(_ValueType.DICT.value)

	@staticmethod
	def _writeArray(output: bytearray, stringList: List[str], useShortStringIndex: bool, l: List[Any]):
		output.extend(_ValueType.ARRAY.value)
		output.extend(Utils.toWritableInt(len(l)))
		for value in l:
			GGDict._writeValue(output, stringList, useShortStringIndex, value)
		output.extend(_ValueType.ARRAY.value)

	@staticmethod
	def _writeString(output: bytearray, stringList: List[str], useShortStringIndex: bool, s: str, addValueType: bool = True):
		if addValueType:
			output.extend(_ValueType.STRING.value)
		if s not in stringList:
			stringList.append(s)
			keyIndex = len(stringList) - 1
		else:
			keyIndex = stringList.index(s)
		output.extend(Utils.toWritableShort(keyIndex) if useShortStringIndex else Utils.toWritableInt(keyIndex))

	@staticmethod
	def _writeInteger(output: bytearray, stringList: List[str], useShortStringIndex: bool, i: int):
		output.extend(_ValueType.INTEGER.value)
		GGDict._writeString(output, stringList, useShortStringIndex, str(i), False)
