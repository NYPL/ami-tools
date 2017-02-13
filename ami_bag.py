import os
import csv
import argparse
import re
import bagit
import jsonschema
from ami_excel import ami_excel
import logging


LOGGER = logging.getLogger(__name__)


class ami_bagValidationError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)

class ami_bag(bagit.Bag):

    def __init__(self, *args, **kwargs):
        super(ami_bag, self).__init__(*args, **kwargs)
        self.data_files = self.payload_entries().keys()
        self.data_dirs = set([os.path.split(path)[0][5:] for path in self.data_files])


    def validate_amibag(self, fast = True, metadata = False):
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
        except ami_bagValidationError as e:
            LOGGER.error("Error in filenames: {0}".format(e.message))
            valid = False

        try:
            self.check_directory_depth()
        except ami_bagValidationError as e:
            LOGGER.error("Error in path names: {0}".format(e.message))
            valid = False

        try:
            self.check_type()
        except ami_bagValidationError as e:
            LOGGER.error("Error in AMI bag type: {0}".format(e.message))
            valid = False

        if self.type == "excel":
            try:
                self.check_structure_excelbag()
            except ami_bagValidationError as e:
                LOGGER.error("Error in bag structure: {0}".format(e.message))
                valid = False

            if metadata:
                try:
                    self.check_metadata_excel()
                except ami_bagValidationError as e:
                    LOGGER.error("Error in bag metadata: {0}".format(e.message))
                    valid = False

        elif self.type == "json":
            try:
                self.check_structure_jsonbag()
            except ami_bagValidationError as e:
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
        self.excel_metadata = [filename for filename in self.data_files if os.path.splitext(filename)[1] == ".xlsx"]

        if not self.excel_metadata:
            self.raise_bagerror("Excel bag does not contain any files with xlsx extension")

        bad_excel = []

        for filename in self.excel_metadata:
            excel = ami_excel(os.path.join(self.path, filename))
            if not excel.validate_workbook():
                bad_excel.append(filename)

        if bad_excel:
            self.raise_bagerror("Excel files contain formatting errors")

        return True


    def add_json_from_excel(self):
        self.excel_metadata = [filename for filename in self.data_files if os.path.splitext(filename)[1] == ".xlsx"]

        for filename in self.excel_metadata:
            excel = ami_excel(os.path.join(self.path, filename))

            output_path = os.path.join(self.path, "data/PreservationMasters")
            excel.convert_amiExcelToJSON(excel.pres_sheetname,
                output_path)
            '''
            if excel.edit_sheetname:
                output_path = os.path.join(self.path, "data/EditMasters")
                excel.convert_amiExcelToJSON(excel.edit_sheetname,
                    output_path)
            '''


    def raise_bagerror(self, msg):
        '''
        lazy error reporting
        '''

        raise ami_bagValidationError(msg)
        logging.error(msg + '\n')
        return False



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
