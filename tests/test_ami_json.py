import unittest
import os

import ami_md.ami_json as aj

pm_json_dir = 'tests/test-data/json-video-bag/PreservationMasters'
pm_json_filename = 'myd_263524_v01_pm.json'
pm_json_path = os.path.join(pm_json_dir, pm_json_filename)

class TestAMIJSON(unittest.TestCase):

  def test_load_json_file(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    self.assertEqual(pm_json.filename, pm_json_filename)
    self.assertTrue(hasattr(pm_json, 'dict'))
    self.assertTrue(pm_json.media_format_type == 'video')

  def test_dont_load_json_file(self):
    pm_json = aj.ami_json(filepath = pm_json_path, load = False)
    self.assertFalse(hasattr(pm_json, 'dict'))

  def test_load_bad_json_file(self):
    not_json_path = pm_json_path.replace('json', 'mov')
    self.assertRaises(aj.AMIJSONError, aj.ami_json,
      filepath = not_json_path)

if __name__ == '__main__':
  unittest.main()
