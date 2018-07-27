import os
import argparse
import subprocess


def main():
	parser = argparse.ArgumentParser()
	parser.description = "rsync a file from repo"
	parser.add_argument("-i", "--uuid",
		help = "uuid of file in repo",
		required = True)
	parser.add_argument("-r", "--repo",
		help = "local path to repo",
		default = "/Volumes/repo/")
	parser.add_argument("-o", "-d", "--destination",
		help = "path to destination",
		default = "/Volumes/video_repository/Working_Storage/")
	args = parser.parse_args()

	uuid_path = '/'.join([args.uuid[0:2], args.uuid[0:4],
		args.uuid[4:8], args.uuid[9:13],
		args.uuid[14:18], args.uuid[19:23],
		args.uuid[24:28], args.uuid[28:32],
		args.uuid[32:34], args.uuid])

	full_path = os.path.join(args.repo, uuid_path)
	rsync_call = ["rsync", "-rtv", "--progress",
		full_path, args.destination]
	subprocess.call(rsync_call)


if __name__ == "__main__":
	main()