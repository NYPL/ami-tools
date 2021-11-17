import unittest
import argparse
import shutil
import os
import tempfile
import pathlib

import get_repo_file


class ProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

        self.objectid = 'ncow421'
        self.uuid = '12345678-3124-2314-1234-123456978102'

        self.uuid_path = self.tmpdir.joinpath('12/1234/5678/3124/2314/1234/1234/5698/81')
        self.uuid_path.mkdir(parents=True)
        self.uuid_path.joinpath(self.uuid).touch()

        self.assets_path = self.tmpdir.joinpath('assets.csv')
        with open(self.assets_path, 'w') as f:
            f.write(f'"name","uuid"\n"myt_{self.objectid}_pm","{self.uuid}"')
        self.assets_path_str = str(self.assets_path)


    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            os.chmod(self.tmpdir, 0o700)
            for dirpath, subdirs, filenames in os.walk(self.tmpdir, topdown=True):
                for i in subdirs:
                    os.chmod(os.path.join(dirpath, i), 0o700)

            shutil.rmtree(self.tmpdir)


    def test_load_assetscsv(self):
        assets = get_repo_file.parse_assets(self.assets_path)

        self.assertTrue(self.objectid in assets.keys())
        self.assertTrue('name', 'uuid' in assets[self.objectid])
  
    def test_bad_assetscsv(self):
        with open(self.assets_path, 'w') as f:
            f.write(f'"nme", "uuid"\n"myt_{self.objectid}_pm", "{self.uuid}"')

        self.assertRaises(ValueError,
            get_repo_file.parse_assets,
            self.assets_path
        )

    def test_extract_objectid(self):
        self.assertTrue(False)

    def test_objectid_notfound(self):
        self.assertTrue(False)

    def test_transform_uuid(self):
        self.assertTrue(False)

    def test_uuid_stringcorrupt(self):
        self.assertTrue(False)

    def test_uuid_pathnotfound(self):
        self.assertTrue(False)

    def test_add_extension(self):
        self.assertTrue(False)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())

        self.objectid = "ncow421"

        self.assets_path = self.tmpdir.joinpath('assets.csv')
        self.assets_path.touch()
        self.assets_path_str = str(self.assets_path)

        self.source_path = self.tmpdir.joinpath('source')
        self.source_path.mkdir()
        self.source_path_str = str(self.source_path)

        self.output_path = self.tmpdir.joinpath('output')
        self.output_path.mkdir()
        self.output_path_str = str(self.output_path)
        
        self.parser = get_repo_file._make_parser()
        

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            os.chmod(self.tmpdir, 0o700)
            for dirpath, subdirs, filenames in os.walk(self.tmpdir, topdown=True):
                for i in subdirs:
                    os.chmod(os.path.join(dirpath, i), 0o700)

            shutil.rmtree(self.tmpdir)

    def test_accept_required(self):
        flagsets = [
            ('--object', '--asset', '--repo', '--destination'),
            ('-i', '-a', '-r', '-d')
        ]

        for flags in flagsets:
            parsed = self.parser.parse_args(
                [flags[0], self.objectid, flags[1], self.assets_path_str,
                flags[2], self.source_path_str, flags[3], self.output_path_str]
            )

            self.assertEquals(parsed.object, [self.objectid])
            self.assertEquals(parsed.assets, self.assets_path_str)

    def test_accept_multiple_objectid(self):
        objectid2 = "234567"

        parsed = self.parser.parse_args(
            ['--object', self.objectid, '-i', objectid2, '--asset', self.assets_path_str,
            '--repo', self.source_path_str, '--destination', self.output_path_str]
        )

        print(parsed.object)
        self.assertEquals(parsed.object, [self.objectid, objectid2])

    def test_require_objectid(self):
        with self.assertRaises(SystemExit):
            self.assertRaises(argparse.ArgumentError,
                self.parser.parse_args(),
                ['--asset', self.assets_path_str]
            )

    def test_objectid_notfilenamified(self):
        objectid = "ncow 421"

        with self.assertRaises(SystemExit):
            self.assertRaises(argparse.ArgumentError,
                self.parser.parse_args,
                ['--object', objectid]
            )

    def test_require_inventorysheet(self):
        with self.assertRaises(SystemExit):
            self.assertRaises(argparse.ArgumentError,
                self.parser.parse_args(),
                ['--object', self.objectid]
            )

    def test_inventorysheet_doesnotexist(self):
        self.assets_path.unlink()

        with self.assertRaises(SystemExit):
            self.assertRaises(argparse.ArgumentError,
                self.parser.parse_args,
                ['--object', self.objectid, '--asset', self.assets_path_str]
            )

    def test_sourcelocation_doesnotexist(self):
        self.source_path.rmdir()

        with self.assertRaises(SystemExit):
            self.assertRaises(argparse.ArgumentError,
                self.parser.parse_args,
                ['--object', self.objectid, '--asset', self.assets_path_str,
                '--repo', self.source_path_str, '--destination', self.output_path_str]
            )    

    def test_outputlocation_doesnotexist(self):
        self.output_path.rmdir()
        
        with self.assertRaises(SystemExit):
            self.assertRaises(argparse.ArgumentError,
                self.parser.parse_args,
                ['--object', self.objectid, '--asset', self.assets_path_str,
                '--repo', self.source_path_str, '--destination', self.output_path_str]
            )