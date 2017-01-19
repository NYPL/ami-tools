import os, argparse, re, csv, glob
from ami_excel import ami_excel
import ami_md_constants

def _make_parser():
  parser = argparse.ArgumentParser()
  parser.description = "check Excel for validity"
  parser.add_argument("-d", "--directory",
    help = "directory of excel files")
  parser.add_argument("-e", "--excel",
    help = "path to an AMI Excel file")
  parser.add_argument("-o", "--output",
    help = "directory to save all json files")
  return parser


def main():
  parser = _make_parser()
  args = parser.parse_args()

  excel_paths = []

  if args.excel:
    excel_paths.append(args.excel)

  if args.directory:
    directory_path = os.path.abspath(args.directory)
    for path in glob.glob("{}*.xls*".format(directory_path)):
      path = os.path.join(directory_path, path)
      excel_paths.append(path)

  if args.output:
    output_path = os.path.abspath(args.output)

  for excel_path in excel_paths:
    excel = ami_excel(excel_path)

    print(excel_path)
    excel.convert_amiExcelToJSON(excel.pres_sheetname,
      ami_md_constants.HEADER_CONVERSION, output_path)


if __name__ == "__main__":
  main()
