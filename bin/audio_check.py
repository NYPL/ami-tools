import os
import argparse
import subprocess


def main():
	parser = argparse.ArgumentParser()
	parser.description = "rsync a file from repo"
	parser.add_argument("-i", "--input_file",
		help = "path to file",
		required = True)
	args = parser.parse_args()

	ffmpeg_call = subprocess.call(['ffmpeg', '-i', 
		args.input_file, '-af', 'asetnsamples=n=44100',
		'-f', 'framemd5', '-vn', '-t', '20', '-'])
	subprocess.call(ffmpeg_call)


if __name__ == "__main__":
	main()
