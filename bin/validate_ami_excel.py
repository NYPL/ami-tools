import argparse
import os
import re
import xlrd
import sys
import logging
from openpyxl import load_workbook
from ami_md.ami_excel import ami_excel

LOGGER = logging.getLogger(__name__)


def _configure_logging(args):
  """
  Give options on how to report progress.
  Requires command line arguments for reporting level and where to save the log file
  """
  log_format = '%(asctime)s - %(levelname)s - %(message)s'
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
    parser.description = "check Excel for validity"
    parser.add_argument("-e", "--excel",
                        help = "path to an AMI Excel file")
    parser.add_argument("-o", "--output",
                        help = "filename to save Excel file if rewritten")
    parser.add_argument('--log', help='The name of the log file')
    parser.add_argument('--quiet', action='store_true')
    return parser


def main():
    parser = _make_parser()
    args = parser.parse_args()

    _configure_logging(args)

    if args.excel:
        excel = ami_excel(args.excel)

    if excel and excel.validate_workbook():
        LOGGER.info("{}: valid".format(args.excel))
    else:
        if args.output:
            wb = load_workbook(args.excel, data_only = True)
            wb.save(args.output)
            new_excel = ami_excel(args.output)
            if new_excel.validate_workbook():
                LOGGER.info("{}: valid".format(args.output))
            else:
                LOGGER.error("{}: invalid".format(args.output))



if __name__ == "__main__":
    main()
