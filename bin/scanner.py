import os
import glob
import sqlite3
import argparse

def _make_parser():
	parser = argparse.ArgumentParser()
	parser.description = "survey designated folder and child folders for files by extensions"

	parser.add_argument("-d", "--directory",
	help = "path of directory to survey",
		required = True
	)
	parser.add_argument("-e", "--extension",
		help = "type of extension to find",
		required = True
	)

	return parser

def main():

	args = _make_parser().parse_args()

	conn = sqlite3.connect('amigrate.db')

	c = conn.cursor()

	dir_to_search = os.path.join(args.directory, '/**/*.{}'.format(args.extension))

	for path in glob.iglob(dir_to_search):
		print(path)

	or command in createTables:
		c.execute(command)

	conn.commit()

	conn.close()



if __name__ == '__main__':
	main()