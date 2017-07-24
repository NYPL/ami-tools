# AMI Tools
[![Build Status](https://travis-ci.org/NYPL/ami-tools.svg?branch=master)](https://travis-ci.org/NYPL/ami-tools)
[![Coverage Status](https://coveralls.io/repos/github/NYPL/ami-tools/badge.svg?branch=master)](https://coveralls.io/github/NYPL/ami-tools?branch=master)

Python3 scripts and classes to help with managing bags of NYPL AMI files

## Installation
Clone the git repo and run the following shell command from inside the directory

```sh
pip3 install .
```

## Tools
Installing the package makes the following tools available from the command line. All scripts include a help dialog.
```sh
script_name.py -h
```

### Data collection
#### survey_drive.py
Generate the following from a mounted drive (or any folder): report of all files, report of all bags, directory with a copy of all presumed metadata (JSON and Excel)

Usage: Survey a drive mounted on a Mac

```sh
survey_drive.py -d /Volumes/drive-name -o path/to/dir/for/reports
```

### Validation Tools
#### validate_ami_bags.py
Check bag Oxums, bag completeness, bag hashes, directory structure, filenames, and metadata (only implemented for Excel)

Usage: Check a directory of bags, default check does not look at metadata or checksums

```sh
validate_ami_bags.py -d path/to/dir/of/bags
```
Usage: Check a single bag, including metadata or checksums

```sh
validate_ami_bags.py -b path/to/bag --metadata --slow
```

#### validate_ami_excel.py
Check if an excel file adheres to the expectations of media ingest

Usage: Check a single Excel file

```sh
validate_ami_bags.py -e path/to/excel/file
```

#### validate_bags.py
Check bag Oxums, bag completeness, and bag hashes (if requested). Default is similar to `bagit.py --validate --fast` except includes completeness check. Less strict than `validate_ami_bags.py`.

Usage: Check a single bag

```sh
validate_bags.py -b path/to/bag --slow
```

* bagit.py - local fork of bagit-python to expose option for completeness checking

Usage: Check bag Oxum and completeness but not hashes

```sh
bagit.py --validate --fast --complete path/to/bag
```

### Bag Management Tools
#### fix_baginfo.py
Update Oxum in bag-info.txt to match actual Oxum

Usage: Check and repair a directory of bag Oxums

```sh
fix_baginfo.py -d path/to/dir/of/bags
```

#### repair_bags.py (in development)
Manage files in bag-payload but not in manifest, either adding them to the manifest or deleting them.

Usage: Add all untracked files to manifest and Oxum

```sh
repair_bags.py -b path/to/bag --addfiles
```

Usage: Delete all untracked file from data/ directory. By default, only the following system files will be deleted: Thumbs.db files, DS_Store files, Appledouble files, and Icon files

```sh
repair_bags.py -b path/to/bag --deletefiles
```

#### convert_excelbag_to_jsonbag.py (in development)
Convert an bag that meets rules for AMI Excel bags to a bag that meets rules for AMI JSON bags

Usage: Convert all bags in a directory from Excel to JSON

```sh
convert_excelbag_to_jsonbag.py -b path/to/bag
```


## Classes
The package also contains classes for implementing further tools

### ami_bag.ami_bag
Extension of the bagit-python Bag class with methods for validation and classification of bags according to NYPL AMI rules

### ami_md.ami_excel
Classes and methods for Excel workbooks and sheets storing metadata about preservation masters, edit masters, and no transfers

Usage: Validate the contents preservation master sheet against the ingest business rules

```python
import ami_md.ami_excel

excel_file = ami_md.ami_excel("path/to/excel.xlsx")
excel_file.pres_sheet.validate_worksheet()
```

### ami_md.ami_json
Methods for loading and manipulating AMI JSON data.

Usage: Convert a valid AMI JSON file to a flat key-value dict

```python
import ami_md.ami_json

json_file = ami_md.ami_json(filepath = "path/to/file.json")
new_dict = json_file.convert_nestedDictToDotKey(json_file)
```

### ami_md.ami_md_constants
Constants used for validating, normalizing, and enhancing metadata, mostly through methods in ami_excel.


## Shell scripts
The package also includes a handful of scripts for utility functions. To install these scripts, users should `chmod +x` and create an appropriate alias for each script.

### bin/collect_metadata.sh
Copy xlsx and json from bags to a another directory for manipulation and analysis

### validate_bags.sh
Validate a directory of bags after network transfer (superseded by validate_ami_bags.py)
