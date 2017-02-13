import os
import argparse
from tqdm import tqdm
import logging
from update_bag import Repairable_Bag


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

    checks = "Running in check mode"


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
            bag = Repairable_Bag(bagpath)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            if not bag.check_baginfo():
                LOGGER.info("Bag info invalid")
                bag.update_baginfo()
            else:
                LOGGER.info("Bag info valid")
            unhashed_files = list(bag.payload_files_not_in_manifest())
            if unhashed_files:
                LOGGER.info("Bag payload includes following files not in manifest: {}".format(unhashed_files))
                bag.add_payload_files_not_in_manifest()
            else:
                LOGGER.info("Bag payload files in manifest")


if __name__ == "__main__":
    main()
