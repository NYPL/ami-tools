import os, argparse, re, csv, glob, logging
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
  parser.add_argument("-d", "--directory",
    help = "directory of excel files")
  parser.add_argument("-e", "--excel",
    help = "path to an AMI Excel file")
  parser.add_argument("-o", "--output",
    help = "directory to save all json files")
  parser.add_argument('--log', help='The name of the log file')
  parser.add_argument('--quiet', action='store_true')
  return parser


def main():
  parser = _make_parser()
  args = parser.parse_args()

  _configure_logging(args)

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
    csv_name = os.path.splitext(os.path.split(excel_path)[1])[0]
    output_path = os.path.join(output_path, csv_name + '.csv')
    excel = ami_excel(excel_path)

    print(excel_path)
    print(output_path)
    excel.pres_sheet.convert_amiExcelToCSV(output_path)


if __name__ == "__main__":
  main()
