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
		techmd = ['base_filename', 'extension', 'format', 'size',
			'date_created', 'audio_codec', 'video_codec']
		for field in techmd:
			self.assertTrue(hasattr(pm_file, field))

	def test_load_nonexistant_media_file(self):
		bad_filepath = pm_mov_path.replace('2', '3')
		with self.assertRaises(Exception) as context:
			pm_file = af.ami_file(filepath = bad_filepath)
		expected_msg = '{} is not a valid filepath'.format(bad_filepath)
		self.assertTrue(expected_msg in str(context.exception))

	def test_load_non_media_file(self):
		non_media_path = pm_mov_path.replace('mov', 'json')
		with self.assertRaises(Exception) as context:
			pm_file = af.ami_file(filepath = non_media_path)
		expected_msg = '{} does not appear to be an accepted audio or video format.'.format(os.path.basename(non_media_path))
		self.assertTrue(expected_msg in str(context.exception))



if __name__ == '__main__':
	unittest.main()
