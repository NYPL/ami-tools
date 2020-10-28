import os, argparse
import pandas as pd
import ami_md.ami_json as aj

dtypes = {
	'digitizationProcess.analogDigitalConverter.serialNumber': object,
	'digitizationProcess.captureSoftware.version': object,
	'digitizationProcess.playbackDevice.serialNumber': object,
	'digitizationProcess.timeBaseCorrector.serialNumber': object,
	'digitizationProcess.phonoPreamp.serialNumber': object,
	'physicalDescription.properties.stockProductID': object
}


def _make_parser():
	parser = argparse.ArgumentParser()
	parser.description = "convert a PAMIdb merge export to JSON records"
	parser.add_argument("-i", "--input",
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

	md = pd.read_csv(args.input, dtype = dtypes, encoding="mac_roman")
	md = md.dropna(axis = 1, how = "all")
	md = md.drop(['asset.fileExt'], axis = 1)

	json_directory = os.path.abspath(args.output)

	for (index, row) in md.iterrows():
		json_tree = aj.ami_json(flat_dict = row.to_dict(),
			schema_version = args.schema)
		json_tree.write_json(json_directory, indent = 4)


if __name__ == "__main__":
	main()
