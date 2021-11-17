#!/usr/bin/env python3

import os
import argparse
import csv
import pathlib
import re
import subprocess

import multiprocessing


def _make_parser():

    def validate_object(id):
        if not re.match(r'^[a-z0-9]+$', id):
            raise argparse.ArgumentTypeError(f'Object ID must have no spaces e.g. ncow 421')
        
        return id


    def validate_file(p):
        path = pathlib.Path(p)

        if not path.is_file():
            raise argparse.ArgumentTypeError(f'File path does not exist: {path}')
        
        return p


    def validate_dir(p):
        path = pathlib.Path(p)

        if not path.is_dir():
            raise argparse.ArgumentTypeError(f'Directory path does not exist: {path}')
        
        return p


    parser = argparse.ArgumentParser()
    parser.description = 'rsync a file from repo'
    parser.add_argument('-i', '--object',
        action='append',
        type = validate_object,
        help='cms id of the object to retrieve files for',
        required=True)
    parser.add_argument('-a', '--assets',
        help='csv of assets in repo',
        type = validate_file,
        default='~/assets.csv')
    parser.add_argument('--uuid',
        action='append',
        help='uuid of file in repo')
    parser.add_argument('-r', '--repo',
        help='local path to repo',
        type = validate_dir,
        default='/Volumes/repo/')
    parser.add_argument('-d', '--destination',
        help='path to destination',
        type = validate_dir,
        default='/Volumes/video_repository/Working_Storage/')

    return parser


def extract_id(filename):
    return filename.split('_')[1]


def parse_assets(path):
    with open(path, mode='r') as file:
        reader = csv.DictReader(file)

        assets_dict = {}
        for row in reader:
            object_id = extract_id(row['name'])

            if not object_id in assets_dict.keys():
                assets_dict[object_id] = []

            assets_dict[object_id].append(row)

    return assets_dict


def get_uuid_path(repo_path, uuid):
    file_path = os.path.join(repo_path, '/'.join([uuid[0:2], uuid[0:4],
            uuid[4:8], uuid[9:13],
            uuid[14:18], uuid[19:23],
            uuid[24:28], uuid[28:32],
            uuid[32:34], uuid]))
    return file_path


def run_rsync(source, dest):
    subprocess.call([
        'rsync', '-tv', '--progress',
        source, dest
    ])

def main():
    parser = _make_parser()
    args = parser.parse_args()

    assets_dict = parse_assets(args.assets)

    in_repo = []
    not_in_repo = []
    for object_id in args.object:
        if object_id in assets_dict.keys():
            for file in assets_dict[object_id]:
                in_repo.append({
                    'object_id': object_id,
                    'filename': file['name'],
                    'repo_path': get_uuid_path(args.repo, file['uuid']),
                })	
        else:
            not_in_repo.append(object_id)


    if not_in_repo:
        print(f'no files for:{not_in_repo}')
    
    for file in in_repo:
        dest = os.path.join(args.destination, file['filename'])
        print(f'Downloading {file["repo_path"]} to {dest}')
        run_rsync(file['repo_path'], dest)


if __name__ == '__main__':
    main()