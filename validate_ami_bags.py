import os
import argparse
from tqdm import tqdm
import logging
from ami_bag import ami_bag


LOGGER = logging.getLogger(__name__)

def _configure_logging(opts):
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    if opts.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    if opts.log:
        logging.basicConfig(filename=opts.log, level=level, format=log_format)
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
    parser.add_argument("--metadata", action='store_true',
                        help = "Validate Excel metadata files")
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
    checks += ", Determing bag type, Checking directory structure, Checking filenames"
    if args.metadata:
        checks += ", Validating Excel metadata files."
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

    for bagpath in tqdm(bags):
        LOGGER.info("Checking: {}".format(bagpath))
        try:
            bag = ami_bag(bagpath)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            if bag.validate_amibag(fast = args.slow, metadata = args.metadata):
                LOGGER.info("Valid {} {} bag: {}".format(bag.type, bag.subtype, bagpath))
            else:
                LOGGER.error("Invalid bag: {}".format(bagpath))


if __name__ == "__main__":
    main()
