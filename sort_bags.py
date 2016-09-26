import os
import csv
import argparse

# find all bag manifests


# parse contents of the manifests

def parse_bagcontents(bagpath, algorithm = "md5"):
    manifest_name = "manifest-" + algorithm + ".txt"
    manifest_path = os.path.join(bagpath, manifest_name)

    detected_delimiter = detect_delimiter(manifest_path)

    files = []

    try:
        with open(manifest_path, 'r') as f:
            for line in f.read().splitlines():
                files.append(line.split(detected_delimiter)[-1])
    except:
        return {}

    filetype_summary = parse_filetypes(files)

    return filetype_summary


def parse_filetypes(files):
    extensions = [file.split('.')[-1] for file in files]
    filetypes = {ext: extensions.count(ext) for ext in extensions}

    return filetypes


def detect_delimiter(manifest_path):
    with open(manifest_path, 'r') as f:
        header = f.readline()
        if header.find(" ") != -1:
            return " "
        if header.find("\t") != -1:
            return "\t"

    return " "

# report bag contents

def _make_parser():
    parser = argparse.ArgumentParser()
    parser.description = "report on bag contents"
    parser.add_argument("-d", "--directory",
                        help = "path to a directory full of bags")
    parser.add_argument("-b", "--bagpath",
                        help = "path to the base directory of the bag")
    return parser

def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    if args.bagpath:
        bags.append = os.path.abspath(args.bagpath)

    if args.directory:
        directory_path = os.path.abspath(args.directory)
        for path in os.listdir(directory_path):
            path = os.path.join(directory_path, path)
            if os.path.isdir(path):
                bags.append(path)

    results = []
    for bagpath in bags:
        bag_summary = parse_bagcontents(bagpath)

        if len(bag_summary) == 0:
            result = "Not a bag"
        elif "xlsx" not in bag_summary:
            result = "Not a valid Excel bag, no xlsx metadata file"
        elif bag_summary["xlsx"] == 1:
            if "tar" in bag_summary:
                result = "Born digital bag"
            elif "wav" in bag_summary and len(bag_summary) == 2:
                result = "Audio bag"
            elif "iso" in bag_summary:
                result = "DVD bag"
            elif "mov" in bag_summary and len(bag_summary) == 2:
                result = "Video bag"
        elif bag_summary["xlsx"] > 1:
            if "mov" in bag_summary and "wav" in bag_summary:
                result = "Audio and video bag"
            elif "mov" in bag_summary and "iso" in bag_summary:
                result = "DVD and video bag"
        else:
            result = "Not sure"

        results.append([os.path.split(bagpath)[1], result])

    with open("bagtypes.csv", "wb") as f:
        writer = csv.writer(f)
        writer.writerows(results)

if __name__ == "__main__":
    main()
