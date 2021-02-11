#!/usr/bin/python 

import os
import argparse
import shutil
from tqdm import tqdm
import logging
from ami_bag.ami_bag import ami_bag
from ami_bag.update_bag import Repairable_Bag
import re

TAG_FILE_PATTERNS = {
    "timecode": {
        "regex": r".*timecodes\.txt$",
        "match": True
    },
    "qctools": {
        "regex": r"xml\.gz$",
        "match": True
    },
    "subs": {
        "regex": r".*\.srt$",
        "match": True
    },
    "cd_cues": {
        "regex": r".*\.cue$",
        "match": True
    }
}


LOGGER = logging.getLogger()

def _configure_logging(args):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    if args.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    if args.log:
        logging.basicConfig(filename=args.log, level=level, format=log_format)
    else:
        logging.basicConfig(level=level, format=log_format)


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.description = "check the completeness, fixity, and content of a bag"
    parser.add_argument("-d", "--directory",
                        nargs='+',
                        help = "Path to a directory full of bags")
    parser.add_argument("-b", "--bagpath",
                        nargs='+',
                        default = None,
                        help = "Path to the base directory of the bag")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('-q', '--quiet', action='store_true')
    return parser

def find_files_to_move(bag):
    tag_files = []

    for payload_file in bag.payload_files():
        for rulename, rule in TAG_FILE_PATTERNS.items():
            if bool(re.search(rule["regex"], payload_file)) == rule["match"]:
                tag_files.append(os.path.join(bag.path, payload_file))

    return tag_files


def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    _configure_logging(args)

    if args.directory:
        for directory in args.directory:
            directory_path = os.path.abspath(directory)
            for root, dirnames, filenames in os.walk(directory_path):
                for dirname in dirnames:
                    if re.match(r'\d\d\d\d\d\d$', dirname):
                        bags.append(os.path.join(root, dirname))

    if args.bagpath:
        for bag in args.bagpath:
            bags.append(os.path.abspath(bag))

    LOGGER.info("Checking {} folder(s).".format(len(bags)))

    if args.quiet:
        LOGGER.setLevel(level=logging.ERROR)

    for bagpath in tqdm(sorted(bags)):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = ami_bag(path = bagpath)
        except Exception as e:
            LOGGER.error("Following error encountered while loading {}: {}".format(bagpath, e))
            continue
        else:
            tag_files = find_files_to_move(bag)

        if not tag_files:
            continue

        LOGGER.info("Moving tag files: {}".format(tag_files))

        tag_folder = os.path.join(bagpath, "tags")
        os.makedirs(tag_folder, exist_ok=True)
        
        for tag_file in tag_files:
            tag_path = os.path.join(tag_folder, os.path.basename(tag_file))
            shutil.move(tag_file, tag_path)
    
        #reload bag to update payload_files
        LOGGER.setLevel(level=logging.INFO)
        LOGGER.info("Updating bag: {}".format(bagpath))
        bag = Repairable_Bag(path = bagpath)

        bag.delete_manifest_files_not_in_payload()


if __name__ == "__main__":
    main()
