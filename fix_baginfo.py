import argparse
import bagit
import os
import shutil

class BagInfo:
    def __init__(self, path = None):
        self.path = os.path.abspath(path)
        try:
            self.bag = bagit.Bag(path)
        except:
            print("not bag")

        self.check_baginfo()


    def check_baginfo(self):
        try:
            self.bag.validate(fast = True)
            self.baginfo_valid = True
        except:
            self.baginfo_valid = False


    def fix_baginfo(self):
        if not "Payload-Oxum-original" in self.bag.info.keys():
            self.bag.info["Payload-Oxum-original"] = self.bag.info["Payload-Oxum"]
        else:
            print("Not copying bag-info.txt. Original already exists.")
        self.bag.info["Payload-Oxum-original"] = self.bag.info["Payload-Oxum"]

        total_bytes = 0
        total_files = 0

        for payload_file in self.bag.payload_files():
            payload_file = os.path.join(self.path, payload_file)
            total_bytes += os.stat(payload_file).st_size
            total_files += 1

        self.bag.info["Payload-Oxum"] = "{0}.{1}".format(total_bytes, total_files)

        try:
            bagit._make_tag_file(os.path.join(self.path, "bag-info.txt"), self.bag.info)
        except:
            print("Do not have permission to overwrite bag-info")
            return False

    else:
        print("Not copying bag-info.txt. Original already exists.")
    self.bag.info["Payload-Oxum-original"] = self.bag.info["Payload-Oxum"]

        try:
            self.bag.validate(fast = True)
        except:
            return False

        return True



def _make_parser():
    parser = argparse.ArgumentParser()
    parser.description = "check the completeness, fixity, and content of a bag"
    parser.add_argument("-d", "--directory",
                        help = "Path to a directory full of bags")
    parser.add_argument("-b", "--bagpath",
                        default = None,
                        help = "Path to the base directory of the bag")
    return parser


def main():
    parser = _make_parser()
    args = parser.parse_args()

    bags = []

    if args.directory:
        directory_path = os.path.abspath(args.directory)
        for path in os.listdir(directory_path):
            path = os.path.join(directory_path, path)
            if os.path.isdir(path):
                bags.append(path)


    if args.bagpath:
        bags.append(os.path.abspath(args.bagpath))

    for bagpath in bags:
        print(bagpath)
        bag = BagInfo(bagpath)
        if not bag.baginfo_valid:
            print("Original oxum: {}".format(bag.bag.info["Payload-Oxum"]))
            if not bag.fix_baginfo():
                print("Could not fix bag-info")
            print("Updated oxum: {}".format(bag.bag.info["Payload-Oxum"]))



if __name__ == "__main__":
    main()
