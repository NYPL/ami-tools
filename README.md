# AMI Tools
Python3 scripts and classes to help with staging AMI material for ingest.

## Installation
Clone the git repo and run the following shell command from inside the directory

```sh
pip3 install .
```

## Tools

### Validation
* validate_ami_bags.py - check if bag adheres to rules for file formats, directory names, bag validity, and metadata
* validate_ami_excel.py - check if an excel file adheres to the expectations of media ingest
* validate_bags.py - validate directories of bags by 0xsum, completeness, and/or hashes, requires local fork of bagit-python
* bagit.py - local fork of bagit-python to expose API for completeness checking
* validate_bags.sh - cron-able script to validate a directory of bags after network transfer (superseded by python version)

### Repair
* fix_baginfo.py - update 0xsum after the addition or deletion of files from a bag
* repair_bag.py - add untracked files in a bag's data directory to the manifest and update other portions of the bag as well

### Bag Creation
* make_bags.sh - bag all directories in current location

### Metadata collecting
* collect_metadata.sh - collect xls and json from punctured bags for local manipulation and analysis
* create_json_from_excel.py - create json from AMI Excel sheets

### Classes
* ami_bag.py - extension of the bagit-python Bag class with methods for validation and classification of bags according to NYPL AMI rules
* ami_excel.py - methods to validate AMI Excel sheets, convert sheets into JSON or CSV, normalize values according to ami_md_constants
