import os
import argparse
from tqdm import tqdm
import logging
from ami_bag.update_bag import Repairable_Bag

file_deletion_rules = rules = {
    "Thumbs.db": {
        "regex": r"3695",
        "match": False
    }
}

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
    parser.add_argument("-a", "--agent",
    				    default = None,
    				    help = "Name of person repairing the bag")
    parser.add_argument('--addfiles', help='Add files not in manifest to the manifest',
                        action='store_true')
    parser.add_argument('--deletefiles', help='Delete files not in manifest from the manifest',
                        action='store_true')
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
            bag = Repairable_Bag(path = bagpath, repairer = args.agent)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            unhashed_files = list(bag.payload_files_not_in_manifest())
            if unhashed_files:
                LOGGER.info("Bag payload includes following files not in manifest: {}".format(unhashed_files))
                if args.addfiles:
                    try:
                        LOGGER.info("Adding untracked files to manifest")
                        bag.add_payload_files_not_in_manifest()
                        LOGGER.info("Untracked files successfully added to manifest.")
                    except:
                        LOGGER.error("Updating process incomplete. Run full validation to check status")
                if args.deletefiles:
                    try:
                        LOGGER.warning("Deleting untracked files from manifest")
                        bag.delete_payload_files_not_in_manifest()
                        LOGGER.info("Untracked files successfully deleted.")
                    except:
                        LOGGER.error("Deletion process incomplete. Run full validation to check status")
            else:
                LOGGER.info("No untracked file in payload directory")
                if not bag.check_baginfo():
                    LOGGER.info("Bag info invalid")
                    bag.update_baginfo()
                else:
                    LOGGER.info("Bag info valid")



if __name__ == "__main__":
    main()
