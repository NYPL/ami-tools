import unittest
import tempfile
import os
import shutil
import ami_bag.bagit as bagit

import ami_bag.ami_bag as ami_bag

class TestNotAnAMIBag(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.mkdtemp()
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)
    shutil.copytree('tests/test-data/unbagged', self.tmpdir)

  def tearDown(self):
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)

  def test_not_valid_bag(self):
    self.assertRaises(ami_bag.bagit.BagError, ami_bag.ami_bag,
      self.tmpdir)

  def test_not_ami_bag(self):
    bagit.make_bag(self.tmpdir)
    self.assertRaises(ami_bag.ami_BagError, ami_bag.ami_bag,
      self.tmpdir)

class TestAMIBag(unittest.TestCase):

  def setUp(self, test_dir = 'tests/test-data/json-video-bag'):
    self.tmpdir = tempfile.mkdtemp()
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)
    shutil.copytree(test_dir, self.tmpdir)

  def tearDown(self):
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)

  def validate(self, bag, *args, **kwargs):
    return bag.validate(*args, **kwargs)

  def test_load_bag(self):
    bag = ami_bag.ami_bag(self.tmpdir)
    attrs = ['data_files', 'data_dirs', 'data_exts',
      'media_filepaths']
    for attr in attrs:
      self.assertTrue(hasattr(bag, attr))


class TestJSONAudioAMIBag(TestAMIBag):

  def setUp(self, test_dir = 'tests/test-data/json-audio-bag'):
    self.tmpdir = tempfile.mkdtemp()
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)
    shutil.copytree(test_dir, self.tmpdir)

if __name__ == '__main__':
    unittest.main()
