import unittest
from unittest import mock
from unittest.mock import patch
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
        self.capture_uuid = 'ca345678-3124-2314-1234-123456978102'

        self.filename = f'myt_{self.objectid}_pm'

        self.uuid_dir_path = self.tmpdir.joinpath(
            '12/1234/5678/3124/2314/1234/1234/5697/81'
        )
        self.uuid_dir_path.mkdir(parents=True)
        self.uuid_path = self.uuid_dir_path.joinpath(self.uuid)
        self.uuid_path.touch()

        self.assets_path = self.tmpdir.joinpath('assets.csv')
        with open(self.assets_path, 'w') as f:
            f.write(
                f'"name","uuid","capture_uuid","type"\n'
                f'"{self.filename}","{self.uuid}","{self.capture_uuid}",""\n'
            )
        self.assets_path_str = str(self.assets_path)

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            os.chmod(self.tmpdir, 0o700)
            for dirpath, subdirs, filenames in (
                os.walk(self.tmpdir, topdown=True)
            ):
                for i in subdirs:
                    os.chmod(os.path.join(dirpath, i), 0o700)

            shutil.rmtree(self.tmpdir)

    def test_load_assetscsv(self):
        assets = get_repo_file.parse_assets(self.assets_path)

        self.assertTrue(self.objectid in assets.keys())
        self.assertTrue(
            all(x in assets[self.objectid][0].keys() for x in ['name', 'uuid'])
        )

    def test_bad_assetscsv(self):
        with open(self.assets_path, 'w') as f:
            f.write(f'"nme", "uuid"\n"myt_{self.objectid}_pm", "{self.uuid}"')

        self.assertRaises(
            ValueError,
            get_repo_file.parse_assets,
            self.assets_path
        )

    def test_extract_objectid(self):
        extracted = get_repo_file.extract_id(f'myt_{self.objectid}_pm')
        self.assertEqual(extracted, self.objectid)

    def test_oldfilename_objectid(self):
        extracted = get_repo_file.extract_id(f'myt{self.objectid}pm')
        self.assertIsNone(extracted)

    def test_retrieve_entries_for_objectid(self):
        entries = get_repo_file.get_object_entries(
            self.objectid,
            get_repo_file.parse_assets(self.assets_path)
        )

        self.assertEqual(len(entries), 1)

        expected_values = [
            ['object_id', self.objectid], ['filename', self.filename],
            ['uuid', self.uuid]
        ]
        for pair in expected_values:
            self.assertTrue(pair[0] in entries[0].keys())
            self.assertEqual(entries[0][pair[0]], pair[1])

    def test_objectid_notfound(self):
        entries = get_repo_file.get_object_entries(
            self.objectid.replace('ncow', 'ncov'),
            get_repo_file.parse_assets(self.assets_path)
        )

        self.assertIsNone(entries)

    def test_transform_uuid(self):
        repo_path = get_repo_file.get_uuid_path(self.uuid)
        self.assertEqual(repo_path, self.uuid_path.relative_to(self.tmpdir))

    def test_uuid_stringcorrupt(self):
        self.assertRaises(
            ValueError,
            get_repo_file.get_uuid_path,
            self.uuid.replace('-', '')
        )

    def test_add_extension(self):
        with open(self.uuid_path, 'wb') as f:
            f.write(b'\x52\x49\x46\x46\x11\x11\x11\x11\x57\x41\x56\x45')
        ext = get_repo_file.get_extension(self.uuid_path)
        self.assertEqual(ext, '.wav')

    def test_unknown_format(self):
        with open(self.uuid_path, 'wb') as f:
            f.write(b'\x52\x48\x46\x46\x11\x11\x11\x11\x57\x41\x56\x45')
        ext = get_repo_file.get_extension(self.uuid_path)
        self.assertEqual(ext, '.unknown')


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
            for dirpath, subdirs, filenames in (
                os.walk(self.tmpdir, topdown=True)
            ):
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
                [
                    flags[0], self.objectid,
                    flags[1], self.assets_path_str,
                    flags[2], self.source_path_str,
                    flags[3], self.output_path_str
                ]
            )

            self.assertEqual(parsed.object, [self.objectid])
            self.assertEqual(parsed.assets, self.assets_path_str)

    def test_accept_multiple_objectid(self):
        objectid2 = "234567"

        parsed = self.parser.parse_args(
            [
                '--object', self.objectid, '-i', objectid2,
                '--asset', self.assets_path_str,
                '--repo', self.source_path_str,
                '--destination', self.output_path_str
            ]
        )

        print(parsed.object)
        self.assertEqual(parsed.object, [self.objectid, objectid2])

    def test_require_objectid(self):
        with self.assertRaises(SystemExit):
            self.assertRaises(
                argparse.ArgumentError,
                self.parser.parse_args(),
                ['--asset', self.assets_path_str]
            )

    def test_objectid_notfilenamified(self):
        objectid = "ncow 421"

        with self.assertRaises(SystemExit):
            self.assertRaises(
                argparse.ArgumentError,
                self.parser.parse_args,
                ['--object', objectid]
            )

    def test_require_inventorysheet(self):
        with self.assertRaises(SystemExit):
            self.assertRaises(
                argparse.ArgumentError,
                self.parser.parse_args(),
                ['--object', self.objectid]
            )

    def test_inventorysheet_doesnotexist(self):
        self.assets_path.unlink()

        with self.assertRaises(SystemExit):
            self.assertRaises(
                argparse.ArgumentError,
                self.parser.parse_args,
                ['--object', self.objectid, '--asset', self.assets_path_str]
            )

    def test_sourcelocation_doesnotexist(self):
        self.source_path.rmdir()

        args = [
            '--object', self.objectid,
            '--asset', self.assets_path_str,
            '--repo', self.source_path_str,
            '--destination', self.output_path_str
        ]

        with self.assertRaises(SystemExit):
            self.assertRaises(
                argparse.ArgumentError,
                self.parser.parse_args,
                args
            )

    def test_outputlocation_doesnotexist(self):
        self.output_path.rmdir()

        args = [
            '--object', self.objectid,
            '--asset', self.assets_path_str,
            '--repo', self.source_path_str,
            '--destination', self.output_path_str
        ]

        with self.assertRaises(SystemExit):
            self.assertRaises(
                argparse.ArgumentError,
                self.parser.parse_args,
                args
            )


class ScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = pathlib.Path(tempfile.mkdtemp())
        self.tmpdir_str = str(self.tmpdir)

        self.objectid = 'ncow421'
        self.uuid = '12345678-3124-2314-1234-123456978102'
        self.capture_uuid = 'ca345678-3124-2314-1234-123456978102'
        self.objectid2 = 'ncov421'
        self.uuid2 = '12345678-3124-2314-1234-123456978101'
        self.capture_uuid2 = 'ca345678-3124-2314-1234-123456978101'

        self.filename = f'myt_{self.objectid}_pm'
        self.filename2 = f'myt_{self.objectid2}_pm'

        self.uuid_dir_path = self.tmpdir.joinpath(
            '12/1234/5678/3124/2314/1234/1234/5697/81'
        )
        self.uuid_dir_path.mkdir(parents=True)
        self.uuid_path = self.uuid_dir_path.joinpath(self.uuid)
        with open(self.uuid_path, 'wb') as f:
            f.write(b'\x52\x49\x46\x46\x11\x11\x11\x11\x57\x41\x56\x45')

        self.uuid_path2 = self.uuid_dir_path.joinpath(self.uuid2)
        with open(self.uuid_path2, 'wb') as f:
            f.write(b'\x51\x49\x46\x46\x11\x11\x11\x11\x57\x41\x56\x45')

        self.assets_path = self.tmpdir.joinpath('assets.csv')
        with open(self.assets_path, 'w') as f:
            f.write('"name","uuid","capture_uuid","type"\n'
                f'"{self.filename}","{self.uuid}","{self.capture_uuid}",""\n'
                f'"{self.filename2}","{self.uuid2}","{self.capture_uuid2}",""\n'
            )

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            os.chmod(self.tmpdir, 0o700)
            for dirpath, subdirs, filenames in os.walk(
                self.tmpdir, topdown=True
            ):
                for i in subdirs:
                    os.chmod(os.path.join(dirpath, i), 0o700)

            #shutil.rmtree(self.tmpdir)

    def test_onefile(self):
        args = [
            'mock',
            '-i', self.objectid,
            '-a', str(self.assets_path),
            '-r', self.tmpdir_str,
            '-d', self.tmpdir_str
        ]
        with mock.patch('sys.argv', args):
            get_repo_file.main()
            self.assertTrue(
                self.tmpdir.joinpath(self.filename)
                .with_suffix('.wav').is_file()
            )

    def test_multifile(self):

        args = [
            'mock',
            '-i', self.objectid,
            '-i', self.objectid2,
            '-a', str(self.assets_path),
            '-r', self.tmpdir_str,
            '-d', self.tmpdir_str
        ]

        with mock.patch('sys.argv', args):
            get_repo_file.main()
            self.assertTrue(
                self.tmpdir.joinpath(self.filename)
                .with_suffix('.wav').is_file()
            )
            self.assertTrue(
                self.tmpdir.joinpath(self.filename2)
                .with_suffix('.unknown').is_file()
            )

    def test_servicefile(self):
        args = [
            'mock',
            '-i', self.objectid,
            '-a', str(self.assets_path),
            '-r', self.tmpdir_str,
            '-s',
            '-d', self.tmpdir_str
        ]


        with mock.patch('sys.argv', args), mock.patch('get_repo_file.run_s3cp') as mock_s3cp:
            # Don't know how to test S3 downloads yet, so skip
            mock_s3cp.return_value = None
            self.uuid_path.rename(self.tmpdir.joinpath(self.filename))

            get_repo_file.main()
            self.assertTrue(
                self.tmpdir.joinpath(self.filename)
                .with_suffix('.wav').is_file()
            )
