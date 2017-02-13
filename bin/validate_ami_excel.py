import argparse
import os
import re
import xlrd
import sys
from openpyxl import load_workbook
from ami_md.ami_excel import ami_excel


def _make_parser():
    parser = argparse.ArgumentParser()
    parser.description = "check Excel for validity"
    parser.add_argument("-e", "--excel",
                        help = "path to an AMI Excel file")
    parser.add_argument("-o", "--output",
                        help = "filename to save Excel file if rewritten")
    return parser


def main():
    parser = _make_parser()
    args = parser.parse_args()

    if args.excel:
        print(args.excel)
        excel = ami_excel(args.excel)

    if excel and excel.validate_workbook():
        print("Validates")
    else:
        print("Does not validate.")
        if args.output:
            wb = load_workbook(args.excel, data_only = True)
            wb.save(args.output)
            new_excel = ami_excel(args.output)
            if new_excel.validate_workbook():
                print("Validates")
            else:
                print("Does not validate.")



if __name__ == "__main__":
    main()
