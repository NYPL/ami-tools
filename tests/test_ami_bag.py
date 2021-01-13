import unittest
import tempfile
import os
import shutil
import glob
import bagit
import json

import ami_bag.ami_bag as ami_bag
import ami_bag.ami_bag_constants as ami_bag_constants


class SelfCleaningTestCase(unittest.TestCase):
	"""TestCase subclass which cleans up self.tmpdir after each test"""

	def setUp(self):
		super(SelfCleaningTestCase, self).setUp()
		self.starting_directory = os.getcwd()
		self.tmpdir = tempfile.mkdtemp()
		if os.path.isdir(self.tmpdir):
			shutil.rmtree(self.tmpdir)
		shutil.copytree('tests/test-data/json-video-bag', self.tmpdir)

	def tearDown(self):
		if os.path.isdir(self.tmpdir):
			# Clean up after tests which leave inaccessible files behind:

			os.chmod(self.tmpdir, 0o700)

			for dirpath, subdirs, filenames in os.walk(self.tmpdir, topdown=True):
				for i in subdirs:
					os.chmod(os.path.join(dirpath, i), 0o700)

			shutil.rmtree(self.tmpdir)

		super(SelfCleaningTestCase, self).tearDown()


class TestNotAnAMIBag(SelfCleaningTestCase):

	def test_not_valid_bag(self):
		bagit.make_bag(self.tmpdir)
		bagit_txt = os.path.join(self.tmpdir, 'bagit.txt')
		os.remove(bagit_txt)
		self.assertRaises(bagit.BagError, ami_bag.ami_bag, path = self.tmpdir)

	def test_incomplete_bag(self):
		bagit.make_bag(self.tmpdir)
		pres_dir = os.path.join(self.tmpdir, 'data/PreservationMasters')
		shutil.rmtree(pres_dir)
		self.assertRaises(ami_bag.ami_bagError, ami_bag.ami_bag,
			path = self.tmpdir)

	def test_no_presmasters(self):
		pres_dir = os.path.join(self.tmpdir, 'PreservationMasters')
		shutil.rmtree(pres_dir)
		bagit.make_bag(self.tmpdir)
		self.assertRaises(ami_bag.ami_bagError, ami_bag.ami_bag,
			path = self.tmpdir)

	def test_no_mediafiles(self):
		for ext in ami_bag_constants.MEDIA_EXTS:
			for filename in glob.glob(self.tmpdir + "/**/*" + ext):
				os.remove(filename)
		bagit.make_bag(self.tmpdir)
		self.assertRaises(ami_bag.ami_bagError, ami_bag.ami_bag,
			path = self.tmpdir)

	def test_no_metadata(self):
		for ext in ['.json', '.xlsx']:
			for filename in glob.glob(self.tmpdir + "/**/*" + ext):
				os.remove(filename)
		bagit.make_bag(self.tmpdir)
		self.assertRaises(ami_bag.ami_bagError, ami_bag.ami_bag,
			path = self.tmpdir)


class TestJSONVideoAMIBag(SelfCleaningTestCase):

	def test_load_bag(self):
		# Every test fixture should be a valid bag
		bagit.make_bag(self.tmpdir)
		with self.assertLogs('ami_bag.ami_bag', 'INFO') as cm:
			bag = ami_bag.ami_bag(path = self.tmpdir)
		expected_msg = 'successfully loaded'
		self.assertTrue(expected_msg in cm.output[0])
		
		attrs = ['data_files', 'data_dirs', 'data_exts',
			'media_filepaths', 'pm_filepaths', 'em_filepaths',
			'sc_filepaths', 'type', 'subtype']
		for attr in attrs:
			self.assertTrue(hasattr(bag, attr))

	def test_valid_bag(self):
		# Every test fixture should be a valid AMI bag
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		bag.check_amibag(metadata = True)
		bag.validate_amibag(metadata = True)
		self.assertTrue(bag.validate_amibag(metadata = True))

	def test_notype_bag(self):
		# Invalid if the bag doesn't map to Excel, JSON, or Excel-JSON
		# Method: Remove all metadata from bag to obscure type classification
		for filename in glob.glob(self.tmpdir + "/**/*"):
				if 'Metadata' in filename or 'json' in filename:
					os.remove(filename)
		bagit.make_bag(self.tmpdir)
		self.assertRaises(ami_bag.ami_bagError, ami_bag.ami_bag,
			path = self.tmpdir)

	def test_nosubtype_bag(self):
		# Valid if the bag doesn't map to known subtype
		# Method: Add impossible folder/extension combo
		new_dir = os.path.join(self.tmpdir, 'EditMasters')
		os.makedirs(new_dir)
		f = os.path.join(new_dir, "ias_atc04_v01_em.tar")
		with open(f, 'w') as r:
			r.write('♡')
		bagit.make_bag(self.tmpdir)
		with self.assertLogs('ami_bag.ami_bag', 'WARN') as cm:
			bag = ami_bag.ami_bag(path = self.tmpdir)

		self.assertTrue(bag.subtype == 'unknown')
		expected_msg = 'recognized subtype'
		self.assertTrue(expected_msg in cm.output[0])
		self.assertFalse(bag.validate_amibag(metadata = False))

	def test_incompleted_bag(self):
		# Invalid if a bag is updated to invalid bagness after load
		# Method: break valid bag after loading
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		bagit_txt = os.path.join(self.tmpdir, 'bagit.txt')
		os.remove(bagit_txt)
		with self.assertLogs('ami_bag.ami_bag', 'WARN') as cm:
			valid_bag = bag.validate_amibag()
		expected_msg = 'Error in bag:'
		self.assertTrue(expected_msg in cm.output[0])
		self.assertFalse(valid_bag)

	def test_invalid_filename(self):
		# Invalid if filenames don't meet expectations
		# Method: Gut characters from the middle of all filenames in payload
		for filename in glob.glob(self.tmpdir + "/**/*"):
			parts = os.path.split(filename)
			basename_parts = parts[1].split('_')
			new_filename = os.path.join(parts[0], basename_parts[0] + '_' + basename_parts[-1])
			os.rename(filename, new_filename)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		self.assertFalse(bag.validate_amibag())

	def test_complex_subobject(self):
		# Invalid if bag has more complex subobjects than faces
		# Method: Add complex subobject tags
		for filename in glob.glob(self.tmpdir + "/**/*"):
			os.rename(filename, filename.replace('_v01_', '_v01r01p01_'))
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		self.assertFalse(bag.validate_amibag())

	def test_deepdirectories(self):
		# Invalid if bag has too many nested folders
		# Method: Add an unsuspected deep folder
		new_dir = os.path.join(self.tmpdir, 'data', 'EditMasters', 'deepdir')
		os.makedirs(new_dir)
		f = os.path.join(new_dir, "iasatc-04partfiles_em.tar")
		with open(f, 'w') as r:
			r.write('♡')
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		self.assertFalse(bag.validate_amibag())

	def test_fileinwrongdir(self):
		# Invalid if file in role different from its filename code
		# Method: move metadata to wrong folder
		pms = glob.glob(self.tmpdir + "/**/*pm")
		for filename in glob.glob(self.tmpdir + "/**/*json"):
			new_path = os.path.join(self.tmpdir, 'PreservationMasters', os.path.basename(filename))
			shutil.move(filename, new_path)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)

		with self.assertLogs('ami_bag.ami_bag', 'ERROR') as cm:
			valid_bag = bag.validate_amibag()
		for path in set(pms):
			stub = os.path.basename(path).rsplit('_', 1)[0]
			self.assertTrue(stub in cm.output[0])
		self.assertFalse(valid_bag)

	def test_unmatchedpm(self):
		# Invalid if bag has non-lonely but unmatched PMs
		# Method: Change all PM names to unmatched
		changed_files = []
		for filename in glob.glob(self.tmpdir + "/**/*"):
			if '_pm.' in filename:
				new_filename = change_filename_division(filename)
				os.rename(filename, new_filename)
				changed_files.append(new_filename)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)

		if bag.sc_filepaths or bag.em_filepaths:
			with self.assertLogs('ami_bag.ami_bag', 'ERROR') as cm:
				valid_bag = bag.validate_amibag()
			for path in set(changed_files):
				stub = os.path.basename(path).rsplit('_', 1)[0]
				self.assertTrue(stub in cm.output[0])
			self.assertFalse(valid_bag)
		else:
			self.assertTrue(bag.validate_amibag())

	def test_unmatchedem(self):
		# Invalid if bag has unmatched EMs
		# Method: Change all EM names to unmatched
		changed_files = []
		for filename in glob.glob(self.tmpdir + "/**/*"):
			if '_em.' in filename:
				new_filename = change_filename_division(filename)
				os.rename(filename, new_filename)
				changed_files.append(new_filename)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)

		if bag.em_filepaths:
			with self.assertLogs('ami_bag.ami_bag', 'ERROR') as cm:
				valid_bag = bag.validate_amibag()

			for path in set(changed_files):
				stub = os.path.basename(path).rsplit('_', 1)[0]
				self.assertTrue(stub in cm.output[0])
			self.assertFalse(valid_bag)
		else:
			self.assertTrue(bag.validate_amibag())

	def test_unmatchedsc(self):
		# Invalid if bag has unmatched SCs
		# Method: Change all SC names to unmatched
		changed_files = []
		for filename in glob.glob(self.tmpdir + "/**/*"):
			if '_sc.' in filename:
				new_filename = change_filename_division(filename)
				os.rename(filename, new_filename)

				changed_files.append(new_filename)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)

		if bag.sc_filepaths:
			with self.assertLogs('ami_bag.ami_bag', 'ERROR') as cm:
				valid_bag = bag.validate_amibag()

			for path in set(changed_files):
				stub = os.path.basename(path).rsplit('_', 1)[0]
				self.assertTrue(stub in cm.output[0])
			self.assertFalse(valid_bag)
		else:
			self.assertTrue(bag.validate_amibag())

	def test_metadata_filename_mismatch(self):
		# Invalid if bag has unmatched metadata
		# Method: Change all JSON names to unmatched
		changed_files = []
		for filename in glob.glob(self.tmpdir + "/*/*"):
			if filename[-4:] == 'json':
				new_filename = change_filename_division(filename)
				os.rename(filename, new_filename)
				changed_files.append(filename)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		
		with self.assertLogs('ami_bag.ami_bag', 'WARN') as cm:
			valid_bag = bag.validate_amibag(metadata = False)

		for path in set(changed_files):
			stub = os.path.basename(path).rsplit('_', 1)[0]
			self.assertTrue(stub in cm.output[0])

		self.assertFalse(valid_bag)

	def test_metadata_manifest_filename_mismatch(self):
		# Invalid if media files aren't matched within metadata file
		# Method: Change all filenames to unmatch from metadata
		changed_files = []
		for filename in glob.glob(self.tmpdir + "/*/*"):
			new_filename = change_filename_division(filename)
			os.rename(filename, new_filename)
			changed_files.append(new_filename)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		# Bag should look valid excepting metadata
		self.assertTrue(bag.validate_amibag(metadata = False))

		with self.assertLogs('ami_bag.ami_bag', 'ERROR') as cm:
			valid_bag = bag.validate_amibag(metadata = True)

		for path in set(changed_files):
			stub = os.path.basename(path).rsplit('_', 1)[0]
			self.assertTrue(stub in cm.output[0])

		self.assertFalse(valid_bag)

	def test_incomplete_json_metadata(self):
		# Invalid if bag metadata does not contain required fields
		# Method: Rewrite json with missing field
		json_path = os.path.join(self.tmpdir,
			'PreservationMasters/myd_263524_v01_pm.json')
		with open(json_path, 'r') as f:
			json_data = json.load(f)
		json_data['technical'].pop('durationHuman', None)
		with open(json_path, 'w') as f:
			json.dump(json_data, f, ensure_ascii=False)
		bagit.make_bag(self.tmpdir)
		bag = ami_bag.ami_bag(path = self.tmpdir)
		self.assertFalse(bag.validate_amibag(metadata = True))

def change_filename_division(filename):
	parts = os.path.split(filename)
	new_filename = os.path.join(parts[0], 'aaa' + parts[1][3:])
	return new_filename


if __name__ == '__main__':
		unittest.main()
