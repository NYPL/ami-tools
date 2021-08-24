#!/usr/bin/env python3

import os
import argparse
import subprocess
import multiprocessing

def rsyncer(rsync_call):
	subprocess.call(rsync_call)

def main():
	parser = argparse.ArgumentParser()
	parser.description = "rsync a file from repo"
	parser.add_argument("-i", "--uuid",
		nargs='+',
		help = "uuid of file in repo",
		required = True)
	parser.add_argument("-r", "--repo",
		help = "local path to repo",
		default = "/Volumes/repo/")
	parser.add_argument("-o", "-d", "--destination",
		help = "path to destination",
		default = "/Volumes/video_repository/Working_Storage/")
	args = parser.parse_args()

	rsync_calls = []
	print(args.uuid)
	for fileid in args.uuid:
		file_path = '/'.join([fileid[0:2], fileid[0:4],
			fileid[4:8], fileid[9:13],
			fileid[14:18], fileid[19:23],
			fileid[24:28], fileid[28:32],
			fileid[32:34], fileid])

		full_path = os.path.join(args.repo, file_path)
		rsync_call = ["rsync", "-rtv", "--progress",
		full_path, args.destination]
		rsync_calls.append(rsync_call)

	count = multiprocessing.cpu_count()
	pool = multiprocessing.Pool(processes=int(count/2))
	r = pool.map_async(rsyncer, rsync_calls)
	r.wait()


if __name__ == "__main__":
	main()