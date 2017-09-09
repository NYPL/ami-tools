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
    self.assertRaises(ami_bag.ami_BagError, ami_bag.ami_bag,
      path = self.tmpdir)

  def test_no_presmasters(self):
    pres_dir = os.path.join(self.tmpdir, 'PreservationMasters')
    shutil.rmtree(pres_dir)
    bagit.make_bag(self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, ami_bag.ami_bag,
      path = self.tmpdir)

  def test_no_mediafiles(self):
    for ext in ami_bag_constants.MEDIA_EXTS:
      for filename in glob.glob(self.tmpdir + "/**/*" + ext):
        os.remove(filename)
    bagit.make_bag(self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, ami_bag.ami_bag,
      path = self.tmpdir)

  def test_no_metadata(self):
    for ext in ['.json', '.xlsx']:
      for filename in glob.glob(self.tmpdir + "/**/*" + ext):
        os.remove(filename)
    bagit.make_bag(self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, ami_bag.ami_bag,
      path = self.tmpdir)


class TestJSONVideoAMIBag(SelfCleaningTestCase):

  def test_load_bag(self):
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    attrs = ['data_files', 'data_dirs', 'data_exts',
      'media_filepaths', 'type', 'subtype']
    for attr in attrs:
      self.assertTrue(hasattr(bag, attr))
    self.assertTrue(bag.type == 'json')
    self.assertTrue(bag.subtype == 'video')

  def test_valid_bag(self):
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    self.assertTrue(bag.validate_amibag(metadata = True))

  def test_incompleted_bag(self):
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    bagit_txt = os.path.join(self.tmpdir, 'bagit.txt')
    os.remove(bagit_txt)
    self.assertFalse(bag.validate_amibag())

  def test_invalid_filename(self):
    pm = os.path.join(self.tmpdir,
      'PreservationMasters/myd_263524_v01_pm.mov')
    new_pm = pm[:-5]
    os.rename(pm, new_pm)
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, bag.check_filenames)
    self.assertFalse(bag.validate_amibag())

  def test_complex_subobject(self):
    pm = os.path.join(self.tmpdir,
      'PreservationMasters/myd_263524_v01_pm.mov')
    new_pm = pm.replace('v01', 'v01r01p01')
    os.rename(pm, new_pm)
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, bag.check_simple_filenames)
    self.assertFalse(bag.validate_amibag())

  def test_deepdirectories(self):
    new_dir = os.path.join(self.tmpdir, 'PreservationMasters/new_dir')
    os.makedirs(new_dir)
    pm_json = os.path.join(self.tmpdir,
      'PreservationMasters/myd_263524_v01_pm.json')
    shutil.move(pm_json, pm_json.replace('/myd', '/new_dir/myd'))
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, bag.check_directory_depth)
    self.assertFalse(bag.validate_amibag())

  def test_metadata_filename_mismatch(self):
    pm_path = os.path.join(self.tmpdir,
      'PreservationMasters/myd_263524_v01_pm.mov')
    new_pm_path = pm_path.replace('_263524_', '_263523_')
    shutil.copy(pm_path, new_pm_path)
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError,
        bag.check_filenames_manifest_and_metadata_json)
    self.assertFalse(bag.validate_amibag(metadata = True))

  def test_bad_json_metadata(self):
    json_path = os.path.join(self.tmpdir,
      'PreservationMasters/myd_263524_v01_pm.json')
    with open(json_path, 'r') as f:
      json_data = json.load(f)
    json_data['technical'].pop('durationHuman', None)
    with open(json_path, 'w') as f:
      json.dump(json_data, f, ensure_ascii=False)
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError,
      bag.check_metadata_json)
    self.assertFalse(bag.validate_amibag(metadata = True))


if __name__ == '__main__':
    unittest.main()
