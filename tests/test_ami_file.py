import unittest
import os

import ami_files.ami_file as af

pm_json_dir = 'tests/test-data/json-video-bag/PreservationMasters'
pm_mov_filename = 'myd_263524_v01_pm.mov'
pm_mov_path = os.path.join(pm_json_dir, pm_mov_filename)

class TestAMIFile(unittest.TestCase):

  def test_load_media_file(self):
    pm_file = af.ami_file(filepath = pm_mov_path)
    self.assertEqual(pm_file.filename, pm_mov_filename)
    self.assertTrue(hasattr(pm_file, 'base_filename'))
    self.assertTrue(pm_file.type == 'video')

  def test_load_nonexistant_media_file(self):
    self.assertRaises(af.AMIFileError, af.ami_file,
      filepath = pm_mov_path.replace('2', '3'))

  def test_load_non_media_file(self):
    self.assertRaises(af.AMIFileError, af.ami_file,
      filepath = pm_mov_path.replace('.mov', '.json'))



if __name__ == '__main__':
  unittest.main()
