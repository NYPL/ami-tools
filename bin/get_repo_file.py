#!/usr/bin/env python3

import os
import argparse
import csv
import pathlib
import re
import subprocess

import multiprocessing

FORMAT_TO_EXT = {
    'DV': '.dv',
    'FLAC': '.flac',
    'Matroska': '.mkv',
    'Quicktime': '.mov',
    'MPEG-4': '.mp4',
    'Wave': '.wav'
}


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
    components = filename.split('_')
    if len(components) == 1:
        return None
    else:
        return components[1]


def parse_assets(path):
    with open(path, mode='r') as file:
        reader = csv.DictReader(file)

        if not all (x in reader.fieldnames for x in ['name', 'uuid']):
            raise ValueError(f'Assets file is missing one or more required header values: name and uuid')

        assets_dict = {}
        for row in reader:
            object_id = extract_id(row['name'])

            if not object_id in assets_dict.keys():
                assets_dict[object_id] = []

            assets_dict[object_id].append(row)

    return assets_dict


def get_object_entries(object_id, assets_dict):
    entries = []
    if object_id in assets_dict.keys():
        for file in assets_dict[object_id]:
            entries.append(
                {
                    'object_id': object_id,
                    'filename': file['name'],
                    'uuid': file['uuid']
                }
            )
    
    if not entries:
        return None

    return entries


def get_uuid_path(uuid):
    if len(uuid.split('-')) != 5:
        raise ValueError(f'UUID is not formatted correctly: {uuid}')

    file_path = pathlib.Path(uuid[0:2]).joinpath(uuid[0:4]) \
            .joinpath(uuid[4:8]).joinpath(uuid[9:13]) \
            .joinpath(uuid[14:18]).joinpath(uuid[19:23]) \
             .joinpath(uuid[24:28]).joinpath(uuid[28:32]) \
            .joinpath(uuid[32:34]).joinpath(uuid)
    return file_path


def get_extension(path):
    format = subprocess.run(
        ['mediainfo', '--Inform=General;%Format%,%FormatProfile%', path],
        capture_output=True
    ).stdout.decode('utf-8').strip().split(',')
    
    if format[1] == 'Quicktime':
        format[0] = 'Quicktime'
        
    if format[0] in FORMAT_TO_EXT.keys():
        ext = FORMAT_TO_EXT[format[0]]
    else:
        ext = 'unknown'

    return ext


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
    for object_id in args.object:
        entries = get_object_entries(object_id, assets_dict)
        if entries:
            in_repo.extend(entries)	
        else:
            print(f'Could not find files listed in CSV for: {object_id}')        

    for file in in_repo:
        print(file)
        repo_path = pathlib.Path(args.repo).joinpath(
            get_uuid_path(file['uuid'])
        )
        dest = pathlib.Path(args.destination).joinpath(file['filename']) \
            .with_suffix(get_extension(repo_path))
        print(f'Downloading {repo_path} to {dest}')
        run_rsync(repo_path, dest)


if __name__ == '__main__':
    main()