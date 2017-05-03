import os
import glob
import argparse
import bagit
from ami_bag.ami_bag import ami_bag
import shutil
import csv
import logging


LOGGER = logging.getLogger(__name__)

def _make_parser():
    parser = argparse.ArgumentParser()
    parser.description = "pull file information, metadata manifest, and bag manifests from a drive"
    parser.add_argument("-d", "--drive",
    help = "path to mounted drive",
        required = True
    )
    parser.add_argument("-o", "--output",
        help = "path to output directory",
        required = True
    )
    parser.add_argument("--overwrite",
        help = "whether to overwrite existing files",
        action = 'store_true'
    )
    return parser

def survey_files(path):
    all_files = glob.iglob(os.path.join(path,'**/*.*'), recursive=True)
    files = []
    bags = []
    metadata = []

    for filepath in all_files:
        filename = os.path.basename(filepath)
        filesize = os.stat(filepath).st_size
        data = [filepath, filename, filesize]
        files.append(data)
        if filename == 'manifest-md5.txt':
            bags.append(os.path.split(filepath)[0])
        if filename.endswith(('.xlsx', '.json')):
            metadata.append(filepath)

    return(files, bags, metadata)

def survey_bag(bag_path):
    try:
        bag = ami_bag(bag_path)
        bag_valid = bag.validate_amibag(metadata = True)
        bag_type = bag.type
        bag_subtype = bag.subtype
    except:
        bag = bagit.Bag(bag_path)
        bag_valid = False
        bag_type = None
        bag_subtype = None

    all_files = glob.iglob(os.path.join(bag_path,'data/**/*.*'), recursive=True)

    bag_files = 0
    bag_size = 0
    for filepath in all_files:
        bag_files += 1
        filesize = os.stat(filepath).st_size
        bag_size += filesize

    bag_metadata = [filename for filename in all_files if filename.endswith(('.xlsx', '.json'))]
    if len(bag_metadata) > 0:
        bag_metadata = ','.join(bag_metadata)
    else:
        bag_metadata = 'no metadata'

    return [bag_path, bag_type, bag_subtype, bag_size, bag_files,  bag_valid]

def main():
    args = _make_parser().parse_args()

    if os.path.exists(args.drive):
        src = os.path.abspath(args.drive)
    else:
        raise OSError("No such directory mounted")

    if os.path.exists(args.output):
        dest = os.path.abspath(args.output)
    else:
        raise OSError("No such directory")

    drive_name = os.path.split(src)[1]


    files, bags, metadata = survey_files(src)

    files_name = drive_name + '_files.csv'
    files_path = os.path.join(dest, files_name)
    if not os.path.exists(files_path) or args.overwrite:
        with open(os.path.join(dest, files_path), 'w') as f:
              csvwriter = csv.writer(f, quoting=csv.QUOTE_ALL)
              csvwriter.writerow(["file_path", "file_name", "file_size"])
              csvwriter.writerows(files)
    else:
        print("File manifest already exists at {}. If you want to replace it, use the --overwrite flag.".format(files_path))

    if len(bags) > 0:
        bag_data = []
        for bag_path in bags:
            bag_info = survey_bag(bag_path)
            bag_data.append(bag_info)
        bags_file = drive_name + '_bags.csv'
        bags_path = os.path.join(dest, bags_file)
        if not os.path.exists(bags_path) or args.overwrite:
            with open(os.path.join(dest, bags_path), 'w') as f:
                  csvwriter = csv.writer(f, quoting=csv.QUOTE_ALL)
                  csvwriter.writerow(["bag_path", "bag_type", "bag_subtype", "bag_size", "bag_files", "bag_mediaingest_valid"])
                  csvwriter.writerows(bag_data)
        else:
            print("Bag manifest already exists at {}. If you want to replace it, use the --overwrite flag.".format(bags_path))

    if len(metadata) > 0:
        metadata_dir = drive_name + '_metadata'
        metadata_dir = os.path.join(dest, metadata_dir)
        if not os.path.exists(metadata_dir) or args.overwrite:
            os.makedirs(metadata_dir)
        else:
            print("Metadata directory already exists at {}. If you want to replace it, use the --overwrite flag.".format(metadata_dir))
        for metadata_path in metadata:
            metadata_filename = os.path.split(metadata_path)[1]
            metadata_copypath = os.path.join(metadata_dir, metadata_filename)
            shutil.copyfile(metadata_path, metadata_copypath)

    print('Drive contains {} files'.format(len(files)))
    print('Drive contains {} bytes of data'.format(sum([i[2] for i in files])))
    print('Drive contains {} bags'.format(len(bags)))
    print('Drive contains {} metadata files'.format(len(metadata)))


if __name__ == '__main__':
  main()
