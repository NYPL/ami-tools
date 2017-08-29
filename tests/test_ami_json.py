import unittest
import os

from ami_md.ami_json import ami_json

pm_json_dir = 'tests/test-data/json-video-bag/PreservationMasters'
pm_json_filename = 'myd_263524_v01_pm.json'
pm_json_path = os.path.join(pm_json_dir, pm_json_filename)

class TestAMIJSON(unittest.TestCase):

  def test_load_json_file(self):
    pm_json = ami_json(filepath = pm_json_path)
    self.assertEqual(pm_json.filename, pm_json_filename)
    self.assertTrue(hasattr(pm_json, 'dict'))

  def test_dont_load_json_file(self):
    pm_json = ami_json(filepath = pm_json_path, load = False)
    self.assertFalse(hasattr(pm_json, 'dict'))

if __name__ == '__main__':
  unittest.main()
