#!/usr/bin/env python3

import csv
import os
import sys
import glob

from ami_bag.ami_bag import ami_bag
from ami_md.ami_json import ami_json
from ami_bag.update_bag import Repairable_Bag
import ami_md.ami_md_constants as ami_md_constants


hash_dict = {}
with open('20200316_mkv_md5') as f:
    hashes = csv.reader(f, delimiter = ' ')
    for row in hashes:
        hash_dict[row[2].split('/')[-1]] = row[0]

def add_mp4(bag_path):
    mp4s = glob.glob(os.path.join(bag_path, 'data', 'ServiceCopies', '*mp4'))
    updateable_bag = Repairable_Bag(path = bag.path, dryrun = False)
    
    for mp4 in mp4s:
        print(mp4)
        new_hash = hash_dict(os.path)
        updateable_bag.entries[mp4] = {'md5': new_hash}
        print(updateable_bag.entries)
        '''
        updateable_bag.add_premisevent(process = "Transcode",
            msg = "Created {} from {}".format(
                 new_file, old_file),
            outcome = "Pass", sw_agent = 'ffmpeg', date = transcode_date,
            human_agent = "Nick Krabbenhoeft")
        '''


def main():
    trans_dir = '/Volumes/lpasync/2_Staging/2014-5/'
    for bag in os.listdir(trans_dir):
        print(bag)
        full_path = os.path.join(trans_dir, bag)
        repair_bag(os.path.join(full_path))
            
if __name__ == '__main__':
	main()