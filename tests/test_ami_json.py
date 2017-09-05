import unittest
import os
import tempfile
import shutil
import warnings

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

  def test_load_invalid_media_filepath(self):
    self.assertRaises(aj.AMIJSONError, aj.ami_json,
      filepath = pm_mov_path,
      media_filepath = pm_mov_path.replace('.mov', '.smooth'))

  def test_validate_valid_json(self):
    pm_json = aj.ami_json(filepath = pm_json_path,
      media_filepath = pm_mov_path)
    self.assertTrue(pm_json.validate_json())

  def test_validate_bad_tech_filename(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['technical']['filename'] = pm_mov_filename
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)

  def test_validate_bad_ref_filename(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['asset']['referenceFilename'] = pm_json.dict['technical']['filename']
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_reffn)

  def test_validate_md_filename_disagreement(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['asset']['referenceFilename'] = pm_mov_filename.replace('2', '3')
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.compare_techfn_reffn)

  def test_validate_techfn_media_filepath_disagreement(self):
    pm_json = aj.ami_json(filepath = pm_json_path,
      media_filepath = pm_mov_path)
    bad_mov_filename = pm_mov_filename.replace('2', '3')
    pm_json.dict['asset']['referenceFilename'] = bad_mov_filename
    pm_json.dict['technical']['filename'] = bad_mov_filename.replace('.mov', '')
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.compare_techfn_media_filename)

  def test_repair_techfn(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['technical']['filename'] = pm_mov_filename
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)
    pm_json.repair_techfn()
    self.assertTrue(pm_json.validate_json())
    self.assertTrue(pm_json.check_techfn)

  def test_unrepairable_techfn(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['technical']['filename'] = pm_mov_filename[:-6]
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)
    with self.assertLogs('ami_md.ami_json', 'ERROR') as cm:
      pm_json.repair_techfn()
    self.assertEqual(cm.output,
      ['ERROR:ami_md.ami_json:Valid technical.filename could not be extracted from myd_263524_v01_'])
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)

  def test_bad_techfn(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['technical']['filename'] = pm_mov_filename.replace('2', '3')[:-3]
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)
    with self.assertLogs('ami_md.ami_json', 'WARN') as cm:
      pm_json.repair_techfn()
    self.assertEqual(cm.output,
      ['WARNING:ami_md.ami_json:Extracted technical filename does not match referenceFilename value.'])
    self.assertTrue(pm_json.check_techfn())
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.compare_techfn_reffn)

  def test_bad_techfn_with_media_filepath(self):
    pm_json = aj.ami_json(filepath = pm_json_path,
      media_filepath = pm_mov_path)
    pm_json.dict['technical']['filename'] = pm_mov_filename.replace('2', '3')[:-3]
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)
    with self.assertLogs('ami_md.ami_json', 'ERROR') as cm:
      pm_json.repair_techfn()
    self.assertEqual(cm.output,
      ['ERROR:ami_md.ami_json:Extracted technical filename does not match provide media filename.'])
    self.assertRaises(aj.AMIJSONError, pm_json.check_techfn)
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.compare_techfn_reffn)

  def test_repair_reffn(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['asset']['referenceFilename'] = pm_mov_filename[:-6]
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_reffn)
    pm_json.repair_reffn()
    self.assertTrue(pm_json.validate_json())
    self.assertTrue(pm_json.check_reffn())
    self.assertTrue(pm_json.compare_techfn_reffn())

  def test_unrepairable_reffn(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['asset']['referenceFilename'] = pm_mov_filename[:-6]
    pm_json.dict['technical']['filename'] = pm_mov_filename[:-6]
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_reffn)
    with self.assertLogs('ami_md.ami_json', 'ERROR') as cm:
      pm_json.repair_reffn()
    self.assertEqual(cm.output,
      ['ERROR:ami_md.ami_json:Valid asset.referenceFilename cannot be created from technical fields: myd_263524_v01_, mov'])
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_reffn)


  def test_validate_missing_techmd_field(self):
    pm_json = aj.ami_json(filepath = pm_json_path)
    pm_json.dict['technical'].pop('durationHuman', None)
    self.assertFalse(pm_json.validate_json())
    self.assertRaises(aj.AMIJSONError, pm_json.check_techmd_fields)




if __name__ == '__main__':
  unittest.main()
