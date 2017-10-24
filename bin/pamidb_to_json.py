import os, argparser
import pandas as pd
import ami_md.ami_json as aj


def _make_parser():
  parser = argparse.ArgumentParser()
  parser.description = "convert a PAMIdb merge export to JSON records"
  parser.add_argument("-i", "--mer", "--input",
    help = "path to a PAMIdb merge export",
    required = True)
  parser.add_argument("-o", "--output",
    help = "directory to save all json files",
    required = True)
  parser.add_argument("-s", "--schema",
    help = "current schema version, preferred format x.y.z",
    default = "2.0.0")
  return parser


def main():
	parser = _make_parser()
  	args = parser.parse_args()

	md = pd.read_csv(args.input)
	md = md.dropna(axis = 1, how = "all").astype(object)
	md = md.drop(['asset.fileExt'], axis = 1)

	json_directory = os.path.abspath(args.output)

	for (index, row) in md.iterrows():
		json_tree = aj.ami_json(flat_dict = row.to_dict(),
			schema_version = args.schema)
		json_tree.write_json(json_directory)


if __name__ == "__main__":
  main()
