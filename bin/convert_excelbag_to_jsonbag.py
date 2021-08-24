#!/usr/bin/env python3

import os
import argparse
from tqdm import tqdm
import logging
from ami_bag.ami_bag import ami_bag
from ami_bag.update_bag import Repairable_Bag


LOGGER = logging.getLogger(__name__)

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
                        help = "Path to a directory full of bags")
    parser.add_argument("-b", "--bagpath",
                        default = None,
                        help = "Path to the base directory of the bag")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('--quiet', action='store_true')
    return parser



def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    _configure_logging(args)

    if args.directory:
        directory_path = os.path.abspath(args.directory)
        for path in os.listdir(directory_path):
            path = os.path.join(directory_path, path)
            if os.path.isdir(path):
                bags.append(path)

    if args.bagpath:
        bags.append(os.path.abspath(args.bagpath))

    LOGGER.info("Checking {} folder(s).".format(len(bags)))

    for bagpath in tqdm(bags):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = ami_bag(bagpath)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            bag.add_json_from_excel()
            update_bag = Repairable_Bag(bagpath)
            update_bag.add_payload_files_not_in_manifest()
            bag = ami_bag(bagpath)
            bag.validate_amibag()


if __name__ == "__main__":
    main()
