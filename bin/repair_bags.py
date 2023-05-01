#!/usr/bin/env python3

import os
import argparse
from tqdm import tqdm
import logging
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
                        nargs = "+",
                        help = '''Path to a directory full of AMI bags. If this is the only arg used,
                        the script checks if there is any files not in manifest, aka untracked files,
                        and check oxum value.''')
    parser.add_argument("-b", "--bagpath",
                        default = None,
                        nargs = "+",
                        help = '''Path to the base directory of the AMI bag. If this is the only arg used,
                        the script checks if there is any files not in manifest, aka untracked files,
                        and check oxum value.''')
    parser.add_argument("-a", "--agent",
    				    default = None,
    				    help = "Name of person repairing the bag")
    parser.add_argument('--addfiles', help='Add payload files not in manifest to the manifest',
                        action='store_true')
    parser.add_argument('--deletefiles', help='Delete payload files not in manifest',
                        action='store_true')
    parser.add_argument('--deletemanifestentries', help='Delete entries from the manifest without payload files',
                        action='store_true')
    parser.add_argument('--write_updates_json_only',
                        help='AFTER repairing JSON, use this arg with bagpath(s) to update manifest, premisjson and tag_manifests',
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
        for directory in args.directory:
            directory_path = os.path.abspath(directory)
            if not os.path.isdir(directory_path):
                continue
            for path in os.listdir(directory_path):
                if len(path) == 6:
                    path = os.path.join(directory_path, path)
                    if os.path.isdir(path):
                        bags.append(path)

    if args.bagpath:
        for bag in args.bagpath:
            bag_path = os.path.abspath(bag)
            bags.append(bag_path)

    LOGGER.info("Checking {} folder(s).".format(len(bags)))

    for bagpath in tqdm(sorted(bags)):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = Repairable_Bag(path = bagpath, repairer = args.agent)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            unhashed_files = list(bag.payload_files_not_in_manifest())
            if unhashed_files:
                LOGGER.warning("Bag payload includes following files not in manifest: {}".format(unhashed_files))
                if args.addfiles:
                    try:
                        LOGGER.warning("Adding untracked files to manifest")
                        bag.add_payload_files_not_in_manifest()
                    except:
                        LOGGER.error("Updating process incomplete. Run full validation to check status")
                if args.deletefiles:
                    try:
                        LOGGER.warning("Deleting untracked files from payload")
                        bag.delete_payload_files_not_in_manifest()
                    except:
                        LOGGER.error("Deletion process incomplete. Run full validation to check status")
            else:
                LOGGER.info("No untracked file in payload directory")
                if not bag.check_oxum():
                    LOGGER.warning("{} Bag info invalid".format(bagpath))
                    if args.bagpath and args.write_updates_json_only:
                        LOGGER.info("writing updates")
                        bag.update_hashes(filename_pattern = r".*\.json$")
                        bag.write_bag_updates()
                else:
                    LOGGER.info("Bag info valid")
            if args.deletemanifestentries:
                if not bag.check_oxum():
                    try:
                        LOGGER.warning("{} Deleting manifest entries without files in the payload".format(bagpath))
                        bag.delete_manifest_files_not_in_payload()
                    except:
                        LOGGER.error("Deletion process incomplete. Run full validation to check status")




if __name__ == "__main__":
    main()
