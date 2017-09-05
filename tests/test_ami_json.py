import unittest
import os
import tempfile
import shutil

import ami_md.ami_json as aj

pm_json_dir = 'tests/test-data/json-video-bag/PreservationMasters'
pm_json_filename = 'myd_263524_v01_pm.json'
pm_mov_filename = 'myd_263524_v01_pm.mov'
pm_json_path = os.path.join(pm_json_dir, pm_json_filename)
pm_mov_path = os.path.join(pm_json_dir, pm_mov_filename)

class TestAMIJSON(unittest.TestCase):

  def test_load_json_file(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    self.assertEqual(pm_json.filename, pm_json_filename)
    self.assertTrue(hasattr(pm_json, 'dict'))
    self.assertTrue(pm_json.media_format_type == 'video')

  def test_dont_load_json_file(self):
    pm_json = aj.ami_json(filepath = pm_json_path, load = False)
    self.assertFalse(hasattr(pm_json, 'dict'))

  def test_load_not_json_file(self):
    self.assertRaises(aj.AMIJSONError, aj.ami_json,
      filepath = pm_mov_path)

  def test_load_bad_json_file(self):
    tmpdir = tempfile.mkdtemp()
    shutil.copy(pm_json_path, tmpdir)
    bad_json_path = os.path.join(tmpdir, pm_json_filename)
    with open(bad_json_path, 'r+') as f:
      f.write(f.read()[1:])
    self.assertRaises(aj.AMIJSONError, aj.ami_json,
      filepath = bad_json_path)

  def test_load_media_filepath(self):
    pm_json = aj.ami_json(filepath = pm_json_path,
      media_filepath = pm_mov_path)
    self.assertTrue(hasattr(pm_json, 'media_filepath'))


if __name__ == '__main__':
  unittest.main()
