import unittest
import tempfile
import os
import shutil
import glob
import bagit

import ami_bag.ami_bag as ami_bag


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
    for ext in ami_bag.EXTS:
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


class TestAMIBag(SelfCleaningTestCase):

  def test_load_bag(self):
    bagit.make_bag(self.tmpdir)
    bag = ami_bag.ami_bag(path = self.tmpdir)
    attrs = ['data_files', 'data_dirs', 'data_exts',
      'media_filepaths', 'type', 'subtype']
    for attr in attrs:
      self.assertTrue(hasattr(bag, attr))
    self.assertTrue(bag.type == 'json')
    self.assertTrue(bag.subtype == 'video')


if __name__ == '__main__':
    unittest.main()
