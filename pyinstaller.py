import os, time

import PyInstaller.__main__

if __name__ == '__main__':
	startTime = time.perf_counter()
	programName = 'MonkeyPack'

	pyInstallerArguments = [
		'main.py',
		'--name=' + programName,
		'--onefile',
		'--clean',  # Always start with a new cache
		'--noconfirm',  # Clean the 'dist' folder
	]
	PyInstaller.__main__.run(pyInstallerArguments)
	print(f"Build took {time.perf_counter() - startTime} seconds")
