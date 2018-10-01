# -*- coding: utf-8 -*-

import codecs
import datetime
import hashlib
import logging
import os
import shutil
import stat
import sys
import tempfile
import unittest
from os.path import join as j
import bagit

import ami_bag.update_bag as update_bag

# don't let < ERROR clutter up test output
logging.basicConfig(filename="test.log", level=logging.DEBUG)


class TestSingleProcessValidation(unittest.TestCase):
  def setUp(self):
    print(os.curdir)
    self.tmpdir = tempfile.mkdtemp()
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)
    shutil.copytree('tests/test-data/unbagged', self.tmpdir)

  def tearDown(self):
    if os.path.isdir(self.tmpdir):
      shutil.rmtree(self.tmpdir)

  def validate(self, bag, *args, **kwargs):
    return bag.validate(*args, **kwargs)

  def test_load_bagmake_bag_sha1_sha256_manifest(self):
    bagit.make_bag(self.tmpdir, checksums=['sha1', 'sha256'])
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    # check that relevant manifests are created
    self.assertTrue(os.path.isfile(j(self.tmpdir, 'manifest-sha1.txt')))
    self.assertTrue(os.path.isfile(j(self.tmpdir, 'manifest-sha256.txt')))
    # check valid with two manifests
    self.assertTrue(self.validate(bag, fast=True))

  def test_update_oxum(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    bag.info['Payload-Oxum'] = '0.0'
    self.assertFalse(bag.is_valid())
    bag.write_baginfo()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertTrue(self.validate(updated_bag))

  def test_payload_file_not_in_manifest(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/._.SYSTEMFILE.db\r")
    with open(f, 'w') as r:
      r.write('♡')
    self.assertEqual(list(bag.payload_files_not_in_manifest()), ['data/._.SYSTEMFILE.db\r'])
    self.assertRaises(bagit.BagValidationError, bag.validate, bag, fast=False)

  def test_add_payload_file_not_in_manifest(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/._.SYSTEMFILE.db\r")
    with open(f, 'w') as r:
      r.write('♡')
    bag.add_payload_files_not_in_manifest()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertTrue(self.validate(updated_bag))

  def test_add_payload_file_not_in_multiple_manifests(self):
    bagit.make_bag(self.tmpdir, checksums=['sha1', 'sha256'])
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/._.SYSTEMFILE.db\r")
    with open(f, 'w') as r:
      r.write('♡')
    bag.add_payload_files_not_in_manifest()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertTrue(self.validate(updated_bag))

  def test_update_hashes(self):
    bagit.make_bag(self.tmpdir, checksums=['sha1', 'sha256'])
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/hello.txt")
    with open(f, 'w') as r:
      r.write('♡')
    bag.update_hashes()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertTrue(self.validate(updated_bag))

  def test_update_hashes_with_no_filter_match(self):
    bagit.make_bag(self.tmpdir, checksums=['sha1'])
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/hello.txt")
    with open(f, 'w') as r:
      r.write('♡')
    bag.update_hashes(filename_pattern = r"\d")
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertEqual(bag.entries["data/hello.txt"], updated_bag.entries["data/hello.txt"])
    self.assertRaises(bagit.BagValidationError, updated_bag.validate, fast=False)

  def test_update_hashes_with_filter_match(self):
    bagit.make_bag(self.tmpdir, checksums=['sha1'])
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/hello.txt")
    with open(f, 'w') as r:
      r.write('♡')
    bag.update_hashes(filename_pattern = r"\w")
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertEqual(bag.entries["data/hello.txt"], updated_bag.entries["data/hello.txt"])
    self.assertTrue(self.validate(updated_bag))

  def test_delete_payload_files_not_in_manifest(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/._.SYSTEMFILE.db\r")
    with open(f, 'w') as r:
      r.write('♡')
    self.assertEqual(list(bag.payload_files_not_in_manifest()), ['data/._.SYSTEMFILE.db\r'])
    bag.delete_payload_files_not_in_manifest()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertTrue(self.validate(updated_bag))

  def test_delete_payload_files_not_in_manifest_with_rules(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/Thumbs.db")
    with open(f, 'w') as r:
      r.write('♡')
    self.assertEqual(list(bag.payload_files_not_in_manifest()), ['data/Thumbs.db'])
    bag.delete_payload_files_not_in_manifest(rules = {"Thumbs.db": {"regex": r"[Tt]humbs\.db$", "match": False}})
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertTrue(updated_bag.is_valid(fast = True))

  def test_do_not_delete_payload_files_not_in_manifest_not_rules(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    f = j(self.tmpdir, "data/._.SYSTEMFILE.db\r")
    with open(f, 'w') as r:
      r.write('♡')
    self.assertEqual(list(bag.payload_files_not_in_manifest()), ['data/._.SYSTEMFILE.db\r'])
    bag.delete_payload_files_not_in_manifest(rules = {"Thumbs.db": {"regex": r"[Tt]humbs\\.db$", "match": False}})
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertEqual(list(updated_bag.payload_files_not_in_manifest()), ['data/._.SYSTEMFILE.db\r'])
    self.assertRaises(bagit.BagValidationError, bag.validate, updated_bag, fast=False)

  def test_record_premis_events(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir)
    bag.add_premisevent(process = "Peek into bag",
      msg = "Just looking around",
      outcome = "Pass", sw_agent = "update_bag.py")
    bag.write_bag_updates()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertEqual(len(updated_bag.premis_events), 1)
    self.assertEqual(set(updated_bag.premis_events[0].keys()),
      set(['Event-Date-Time', 'Event-Type', 'Event-Detail-Information',
      'Event-Outcome', 'Event-Software-Agent']))

  def test_record_premis_default_human_agent(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir, repairer = "Smokey Yunick")
    bag.add_premisevent(process = "Peek into bag",
      msg = "Just looking around", outcome = "Pass",
      sw_agent = "update_bag.py")
    bag.write_bag_updates()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertEqual(updated_bag.premis_events[0]['Event-Human-Agent'],
      "Smokey Yunick")

  def test_record_premis_nondefault_human_agent(self):
    bagit.make_bag(self.tmpdir)
    bag = update_bag.Repairable_Bag(path = self.tmpdir, repairer = "Smokey Yunick")
    bag.add_premisevent(process = "Peek into bag",
      msg = "Just looking around", outcome = "Pass",
      sw_agent = "update_bag.py", human_agent = "Yogi Bear")
    bag.write_bag_updates()
    updated_bag = update_bag.Repairable_Bag(path = self.tmpdir)
    self.assertEqual(updated_bag.premis_events[0]['Event-Human-Agent'],
      "Yogi Bear")

class TestMultiprocessValidation(TestSingleProcessValidation):

    def validate(self, bag, *args, **kwargs):
        return super(TestMultiprocessValidation, self).validate(bag, *args, processes=2, **kwargs)


if __name__ == '__main__':
  unittest.main()
