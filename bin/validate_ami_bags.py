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
    parser = argparse.ArgumentParser(description="Check if an AMI bag meets specifications")
    parser.add_argument("-d", "--directory", nargs='+', help="Path to a directory full of bags")
    parser.add_argument("-b", "--bagpath", nargs='+', default=None, help="Path to the base directory of the bag")
    parser.add_argument("--slow", action='store_false', help="Recalculate hashes (very slow)")
    parser.add_argument("--metadata", action='store_true', help="Validate Excel metadata files")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('-q', '--quiet', action='store_true')
    return parser

def log_checks(args):
    checks = """Performing the following validations:
    Checking Oxums,
    Checking bag completeness,
    """
    if not args.slow:
        checks += "Recalculating hashes,\n"
    checks += """Determining bag type,
    Checking directory structure,
    Checking filenames
    """
    if args.metadata:
        checks += "Validating Excel/JSON metadata files against files\n"
    
    LOGGER.info(checks)
    LOGGER.info("""To interpret log messages:
    A WARNING means the bag is valid but has features that may need double-checking. It's most useful for legacy AMI bag conversion.
    An ERROR means the bag is out of spec and cannot be ingested.
    A CRITICAL means the script has failed. The bag may be in or out of spec.
    """)

def process_directory(directory, args):
    print("Now checking this directory:", directory)
    directory_path = os.path.abspath(directory)
    bags = []
    for root, dirnames, filenames in os.walk(directory_path):
        for dirname in dirnames:
            if re.match(r'\d\d\d\d\d\d$', dirname):
                bags.append(os.path.join(root, dirname))

    if not bags:
        LOGGER.info("No valid bag directories found in: {}".format(directory_path))
        return {'directory': directory_path, 'summary': "No valid bag directories found"}

    return process_bags(bags, args, directory_path)

def process_single_bag(bagpath, args):
    print("Now checking this bag:", bagpath)
    bagpath = os.path.abspath(bagpath)
    return process_bags([bagpath], args, bagpath)

def process_bags(bags, args, directory_path):

    # Log the number of bags or folders being processed
    LOGGER.info("Checking {} folder(s)".format(len(bags)))

    if args.quiet:
        LOGGER.setLevel(level=logging.ERROR)

    warning_bags = []
    error_bags = []
    valid_bags = []

    for bagpath in tqdm(sorted(bags)):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = ami_bag(path=bagpath)
            warning, error = bag.check_amibag(fast=args.slow, metadata=args.metadata)

            if warning:
                LOGGER.warning("Bag may have issues (see warnings above): {}".format(bagpath))
                warning_bags.append(os.path.basename(bagpath))

            if error:
                LOGGER.error("Invalid bag: {}".format(bagpath))
                error_bags.append(os.path.basename(bagpath))
            else:
                valid_bags.append(os.path.basename(bagpath))
        except Exception as e:
            LOGGER.error("Following error encountered while loading {}: {}".format(bagpath, e))
            error_bags.append(os.path.basename(bagpath))

    return {
        'directory': directory_path,
        'warning_bags': warning_bags,
        'error_bags': error_bags,
        'valid_bags': valid_bags,
        'total_bags': len(bags)
    }

def log_summary(results):

    LOGGER.setLevel(level=logging.INFO)
    
    for result in results:
        print("")
        LOGGER.info("Summary for directory: {}".format(result['directory']))
        if 'summary' in result:
            LOGGER.info(result['summary'])
        else:
            total_bags = result['total_bags']
            error_bags = result['error_bags']
            warning_bags = result['warning_bags']
            valid_bags = result['valid_bags']

            if error_bags:
                LOGGER.info("{} of {} bags are NOT ready for ingest".format(len(error_bags), total_bags))
                LOGGER.info("The following bags are NOT ready for media ingest: " + ", ".join(error_bags))
            if warning_bags:
                LOGGER.info("{} of {} bags are ready for ingest, but may have issues".format(len(warning_bags), total_bags))
                LOGGER.info("The following bags are ready for media ingest, but may have issues: " + ", ".join(warning_bags))
            if valid_bags:
                LOGGER.info("{} of {} bags are ready for ingest".format(len(valid_bags), total_bags))
                LOGGER.info("The following bags are ready for media ingest: " + ", ".join(valid_bags))


def main():
    parser = _make_parser()
    args = parser.parse_args()
    _configure_logging(args)
    log_checks(args)

    results = []

    if args.directory:
        for directory in args.directory:
            directory_result = process_directory(directory, args)
            if directory_result:
                results.append(directory_result)

    if args.bagpath:
        for bagpath in args.bagpath:
            bagpath_result = process_single_bag(bagpath, args)
            if bagpath_result:
                results.append(bagpath_result)

    log_summary(results)

if __name__ == "__main__":
    main()
