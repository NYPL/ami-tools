#!/usr/bin/env python3

import os
import argparse
from tqdm import tqdm
import logging
from bagit import Bag


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
    parser.add_argument("--slow", action='store_false',
                        help = "Recalculate hashes (very slow)")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('--quiet', action='store_true')
    return parser



def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    _configure_logging(args)

    checks = "Performing the following validations: Checking 0xums, Checking bag completeness"
    if not args.slow:
        checks += ", Recalculating hashes"
    LOGGER.info(checks)


    if args.directory:
        directory_path = os.path.abspath(args.directory)
        for path in os.listdir(directory_path):
            path = os.path.join(directory_path, path)
            if os.path.isdir(path):
                bags.append(path)

    if args.bagpath:
        bags.append(os.path.abspath(args.bagpath))

    LOGGER.info("Checking {} folder(s).".format(len(bags)))

    if args.quiet:
        LOGGER.setLevel(level=logging.ERROR)

    error_bags = []
    valid_bags = []
    for bagpath in tqdm(bags):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = Bag(bagpath)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            try:
                bag.validate(fast = args.slow)
            except:
                LOGGER.error("{}: invalid".format(bagpath))
                error_bags.append(os.path.basename(bagpath))
            else:
                LOGGER.info("{}: valid".format(bagpath))
                valid_bags.append(os.path.basename(bagpath))

    LOGGER.setLevel(level=logging.INFO)
    if error_bags:
        LOGGER.info("{} of {} bags are invalid".format(len(error_bags), len(bags)))
        LOGGER.info("The following bags are valid: {}".format(", ".join(error_bags)))
    if valid_bags:
        LOGGER.info("{} of {} bags are valid".format(len(valid_bags), len(bags)))
        LOGGER.info("The following bags are invalid: {}".format(", ".join(valid_bags)))


if __name__ == "__main__":
    main()
