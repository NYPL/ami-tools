#!/usr/bin/python 

import os
import argparse
from tqdm import tqdm
import logging
from ami_bag.ami_bag import ami_bag
import re


LOGGER = logging.getLogger()

def _configure_logging(args):
    log_format = "%(name)s: %(asctime)s - %(levelname)s - %(message)s"
    if args.log:
        logging.basicConfig(filename=args.log, level=logging.INFO, format=log_format)
    else:
        logging.basicConfig(level=logging.INFO, format=log_format)


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.description = "check if an AMI bag meets specifications"
    parser.add_argument("-d", "--directory",
                        nargs='+',
                        help = "Path to a directory full of bags")
    parser.add_argument("-b", "--bagpath",
                        nargs='+',
                        default = None,
                        help = "Path to the base directory of the bag")
    parser.add_argument("--slow", action='store_false',
                        help = "Recalculate hashes (very slow)")
    parser.add_argument("--metadata", action='store_true',
                        help = "Validate Excel metadata files")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('-q', '--quiet', action='store_true')
    return parser



def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    _configure_logging(args)

    checks = """Performing the following validations:
    Checking 0xums,
    Checking bag completeness,
    """
    if not args.slow:
        checks += "Recalculating hashes,\n"
    checks += """Determing bag type,
    Checking directory structure,
    Checking filenames
    """
    if args.metadata:
        checks += """Validating Excel/JSON metadata files against files
    """
    LOGGER.info(checks)
    LOGGER.info("""To interpret log messages:
    A WARNING means the bag is out of spec but can be ingested
    An ERROR means the bag is out of spec and cannot be ingested
    A CRITICAL means the script has failed. The bag may be in or out of spec.
    """)


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

    warning_bags = []
    error_bags = []
    valid_bags = []
    for bagpath in tqdm(sorted(bags)):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = ami_bag(path = bagpath)
        except Exception as e:
            LOGGER.error("Following error encountered while loading {}: {}".format(bagpath, e))
            error_bags.append(os.path.basename(bagpath))
        else:
            try:
                warning, error = bag.check_amibag(fast = args.slow, metadata = args.metadata)

                if warning:
                    LOGGER.warning("Bag may have issues (see warnings above): {}".format(bagpath))
                    warning_bags.append(os.path.basename(bagpath))

                if error:
                    LOGGER.error("Invalid bag: {}".format(bagpath))
                    error_bags.append(os.path.basename(bagpath))
                else:
                    valid_bags.append(os.path.basename(bagpath))
            except:
                LOGGER.error('ami-tools issue for {}'.format(bagpath))
                error_bags.append(os.path.basename(bagpath))

    LOGGER.setLevel(level=logging.INFO)
    if error_bags:
        LOGGER.info("{} of {} bags are not ready for ingest".format(len(error_bags), len(bags)))
        LOGGER.info("The following bags are not ready for media ingest: {}".format(", ".join(error_bags)))
    if warning_bags:
        LOGGER.info("{} of {} bags are ready for ingest, but may have issues (see warnings above)".format(len(warning_bags), len(bags)))
        LOGGER.info("The following bags are ready for media ingest, but may have issues (see warnings above): {}".format(", ".join(warning_bags)))
    if valid_bags:
        LOGGER.info("{} of {} bags are ready for ingest".format(len(valid_bags), len(bags)))
        LOGGER.info("The following bags are ready for media ingest: {}".format(", ".join(valid_bags)))



if __name__ == "__main__":
    main()
