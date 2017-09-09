import os
import argparse
from tqdm import tqdm
import logging
from ami_bag.ami_bag import ami_bag
from ami_md.ami_json import ami_json
from ami_bag.update_bag import Repairable_Bag
import re
import sys


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
    parser.description = "Repair common problems with json metadata in AMI bags"
    parser.add_argument("-d", "--directory",
                        help = "Path to a directory full of AMI bags")
    parser.add_argument("-b", "--bagpath",
                        default = None,
                        help = "Path to the base directory of the AMI bag")
    parser.add_argument("-p", "--repairer",
                        default = None,
                        help = "Name of person running the tool.")
    parser.add_argument("--filenames", action='store_true',
                        help = "Fix common errors in asset.referenceFilename and technical.filename")
    parser.add_argument("--techmd", action='store_true',
                        help = "Fix common errors in technical md field by rerunning mediainfo")
    parser.add_argument("--dryrun", action='store_true',
                        help = "Do not perform any of the flagged repairs")
    parser.add_argument("--validate", action='store_true',
                        help = "Run a quick validation on bag after repair")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('--quiet', action='store_true')
    return parser


def repair_bag_filenamemd(bag, repairer, dryrun):
    media_files_filenames = set([os.path.basename(path) for path in bag.media_filepaths])

    repaired_fn = []
    for filename in bag.metadata_files:
        repaired = False
        json_path = os.path.join(bag.path, filename)
        json = ami_json(filepath = json_path)

        try:
            json.check_techfn()
        except:
            if json.repair_techfn():
                repaired = True

        try:
            json.check_reffn()
        except:
            if json.repair_reffn():
                repaired = True

        reffn = json.dict["asset"]["referenceFilename"]
        techfn = json.dict["technical"]["filename"] + '.' + json.dict["technical"]["extension"]

        if repaired:
            if (reffn in media_files_filenames and
                techfn in media_files_filenames):
                if not dryrun:
                    json.write_json(os.path.split(json_path)[0])
                    repaired_fn.append(json.filename)
            else:
                LOGGER.error("Filenames still not great, not writing changes to file for {}".format(
                    filename))

    if repaired_fn:
        updateable_bag = Repairable_Bag(bag.path, repairer = repairer, dryrun = dryrun)
        updateable_bag.add_premisevent(process = "Repair Metadata",
            msg = "Repaired filename fields: {}".format(
                ", ".join(repaired_fn)),
            outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)
        updateable_bag.update_hashes(filename_pattern = r"json")


def repair_bag_techmd(bag, repairer, dryrun):
    media_files_filenames = set([os.path.basename(path) for path in bag.media_filepaths])

    updated_json = []

    for filename in bag.metadata_files:
        json_path = os.path.join(bag.path, filename)
        json = ami_json(filepath = json_path)

        media_filepath = os.path.join(os.path.split(json.path)[0],
            json.dict["asset"]["referenceFilename"])
        json.set_mediafilepath(media_filepath)

        try:
            json.check_techmd_values()
        except:
            json.repair_techmd()
            updated_json.append(json.filename)
            if not dryrun:
                json.write_json(os.path.split(json_path)[0])

    if updated_json:
        updateable_bag = Repairable_Bag(bag.path, repairer = repairer, dryrun = dryrun)
        updateable_bag.add_premisevent(process = "Repair Metadata",
            msg = "Regenerated tech md fields with MediaInfo: {}".format(
                ", ".join(updated_json)),
            outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)
        updateable_bag.update_hashes(filename_pattern = r"json")


def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    _configure_logging(args)

    checks = "Performing these repairs: "
    check_list = []
    if args.filenames:
        check_list.append("filename metadata")
    checks = checks + ", ".join(check_list)
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

    for bagpath in bags:
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = ami_bag(bagpath)
        except:
            LOGGER.error("{}: Not an AMI bag".format(bagpath))
        if args.filenames:
            repair_bag_filenamemd(bag, args.repairer, args.dryrun)
            bag._open()
        if args.techmd:
            repair_bag_techmd(bag, args.repairer, args.dryrun)
            bag._open()


if __name__ == "__main__":
    main()
