import os
import csv
import argparse
import re
import bagit
import jsonschema
from validate_excel import AMI_Excel
import fix_baginfo
from tqdm import tqdm
import logging


LOGGER = logging.getLogger(__name__)


class AMI_BagValidationError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class AMI_Bag(bagit.Bag):

    def __init__(self, *args, **kwargs):
        super(AMI_Bag, self).__init__(*args, **kwargs)
        self.data_files = self.payload_entries().keys()
        self.data_dirs = set([os.path.split(path)[0][5:] for path in self.data_files])


    def validate_AMI_bag(self, fast = True, metadata = False):
        '''
        run each of the validation checks against an AMI Bag
        '''

        valid = True
        try:
            self.validate(fast = fast, complete = fast)
        except bagit.BagValidationError as e:
            LOGGER.error("Error in bag: {0}".format(e.message))
            valid = False

        try:
            self.check_filenames()
        except AMI_BagValidationError as e:
            LOGGER.error("Error in filenames: {0}".format(e.message))
            valid = False

        try:
            self.check_directory_depth()
        except AMI_BagValidationError as e:
            LOGGER.error("Error in path names: {0}".format(e.message))
            valid = False

        try:
            self.check_type()
        except AMI_BagValidationError as e:
            LOGGER.error("Error in AMI bag type: {0}".format(e.message))
            valid = False

        if self.type == "excel":
            try:
                self.check_structure_excelbag()
            except AMI_BagValidationError as e:
                LOGGER.error("Error in bag structure: {0}".format(e.message))
                valid = False

            if metadata:
                try:
                    self.check_metadata_excel()
                except AMI_BagValidationError as e:
                    LOGGER.error("Error in bag metadata: {0}".format(e.message))
                    valid = False

        elif self.type == "json":
            try:
                self.check_structure_jsonbag()
            except AMI_BagValidationError as e:
                LOGGER.error("Error in AMI bag type: {0}".format(e.message))
                valid = False

        return valid


    def check_filenames(self):
        bad_filenames = []

        for filename in self.data_files:
            if not re.search(r"[\w]+\.\w+$", os.path.split(filename)[1]):
                bad_filenames.append(filename)

        if bad_filenames:
            self.raise_bagerror("Illegal characters in the following filenames - {}".format(bad_filenames))

        return True

    def check_directory_depth(self):
        bad_dirs = []

        for dir_path in self.data_dirs:
            if re.search(r"/", dir_path):
                bad_dirs.append(dir_path)

        if bad_dirs:
            self.raise_bagerror("Too many levels of directories in data/ - {}".format(bad_dirs))

        return True


    def check_type(self):
        self.type = None

        if "Metadata" in self.data_dirs:
            self.type = "excel"
        if any(re.search(r"(PreservationMasters|EditMasters|ServiceCopies)/\w+\.json$", filename) for filename in self.data_files):
            self.type = "json"

        if not self.type:
            self.raise_bagerror("Bag is not an Excel bag or JSON bag")

        self.data_exts = set([os.path.splitext(filename)[1].lower() for filename in self.data_files])
        self.subtype = None

        return True


    def compare_content(self, expected_exts):
        if not expected_exts >= self.data_exts:
            return False
        return True


    def compare_structure(self, expected_dirs):
        if not expected_dirs >= self.data_dirs:
            return False
        return True


    def check_structure_excelbag(self):

        expected_dirs = set(["Metadata", "PreservationMasters", "EditMasters", "ArchiveOriginals", "ProjectFiles"])
        if not self.compare_structure(expected_dirs):
            self.raise_bagerror("Excel bags may only have the following directories\nFound: {0}\nExpected: {1}".format(self.data_dirs, expected_dirs))

        if (self.compare_structure(set(["Metadata", "PreservationMasters"])) and
            self.compare_content(set([".mov", ".xlsx"]))):
            self.subtype = "video"
        elif (self.compare_structure(set(["Metadata", "PreservationMasters"])) and
              self.compare_content(set([".iso", ".xlsx"]))):
            self.subtype = "dvd"
        elif (self.compare_structure(set(["Metadata", "PreservationMasters", "EditMasters"])) and
              self.compare_content(set([".wav", ".xlsx"]))):
            self.subtype = "audio"
        elif (self.compare_structure(set(["Metadata", "PreservationMasters"])) and
              self.compare_content(set([".wav", ".xlsx"]))):
            self.subtype = "audio w/o edit masters"
        elif (self.compare_structure(set(["Metadata", "ArchiveOriginals", "PreservationMasters", "EditMasters", "ProjectFiles"])) and
              self.compare_content(set([".tar", ".mov", ".xlsx", ".fcp", ".prproj"]))):
            self.subtype = "born-digital video"
        elif (self.compare_structure(set(["Metadata", "ArchiveOriginals", "EditMasters"])) and
              self.compare_content(set([".wav", ".xlsx"]))):
            self.subtype = "born-digital audio"

        if not self.subtype:
            self.raise_bagerror("Bag does not match an existing profile for Excel bags\nExtensions: {0}\nDirectories: {1}".format(self.data_exts, self.data_dirs))

        return True


    def check_structure_jsonbag(self):
        expected_dirs = set(["PreservationMasters", "ServiceCopies", "EditMasters", "ArchiveOriginals"])

        if not self.compare_structure(expected_dirs):
            self.raise_bagerror("JSON bags may only have the following directories - {}".format(expected_dirs))
        if (self.compare_structure(set(["Metadata", "PreservationMasters", "ServiceCopies"])) and
            self.compare_content(set([".mov", ".json", ".mp4", ".jpeg"]))):
            self.subtype = "video"
        if (self.compare_structure(set(["Metadata", "PreservationMasters", "EditMasters"])) and
            self.compare_content(set([".wav", ".json", ".jpeg"]))):
            self.subtype = "video"

        return True


    def check_metadata_excel(self):
        self.metadata_files = [filename for filename in self.data_files if os.path.splitext(filename)[1] == ".xlsx"]

        if not self.metadata_files:
            self.raise_bagerror("Excel bag does not contain any files with xlsx extension")

        bad_excel = []

        for filename in self.metadata_files:
            excel = AMI_Excel(os.path.join(self.path, filename))
            if not excel.validate():
                bad_excel.append(filename)

        if bad_excel:
            self.raise_bagerror("Excel files contain formatting errors")

        return True


    def raise_bagerror(self, msg):
        '''
        lazy error reporting
        '''

        raise AMI_BagValidationError(msg)
        logging.error(msg + '\n')
        return False

'''
def validate_structure(bag):

        if excel_bag:
            elif filetypes["xlsx"] > 1:
                if "mov" in filetypes and "wav" in filetypes:
                    content = "audio and video"
                elif "mov" in filetypes and "iso" in filetypes:
                    content = "dvd and video"
            else:
                LOGGER.error("hello")
                content, structure = "unknown", "invalid"

        elif json_bag:
            bag_type = "json"
            if len(filetypes.keys()) == 2 and "wav" in filetypes:
                content = "audio"
                if filetypes["wav"] == filetypes["json"]:
                    wav_files = [ re.search(r"(\w_v0\df0\d)", filename)[0] for filename in bag_files if filename.endswith('wav') ]
                    stem_counts = {stem: wav_files.count(stem) for stem in wav_files}
                    if all(x >= 2 for x in stem_counts.values()):
                        structure = "valid"
            if len(filetypes.keys()) == 3:
                if ("mov" in filetypes and "mp4" in filetypes and
                    filetypes["mov"] == filetypes["mp4"] and
                    filetypes["mp4"] == 2 * filetypes["json"]):
                    content = "video"
                    structure = "valid"
                if ("iso" in filetypes and "mp4" in filetypes and
                    filetypes["iso"] == filetypes["mp4"] and
                    filetypes["mp4"] == 2 * filetypes["json"]):
                    content = "dvd"
                    structure = "valid"
                else:
                    LOGGER.error("hello")
                    content, structure = "unknown", "invalid"


    else:
        bag_type, content, structure = "unknown", "unknown", "unknown"

    return bag_type, content, structure
'''

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
            bag = AMI_Bag(bagpath)
        except:
            LOGGER.error("{}: Not a bag".format(bagpath))
        else:
            if bag.validate_AMI_bag(fast = args.slow, metadata = args.metadata):
                LOGGER.info("Valid {} {} bag: {}".format(bag.type, bag.subtype, bagpath))
            else:
                LOGGER.error("Invalid bag: {}".format(bagpath))


if __name__ == "__main__":
    main()
