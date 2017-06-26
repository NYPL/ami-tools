import argparse
import ami_bag.bagit as bagit
import os
import shutil
import datetime
import re
import logging
import json

SYSTEM_FILE_PATTERNS = {
    "Thumbs.db": {
        "regex": r"[Tt]humbs\.db$",
        "match": False
    },
    "DS_Store": {
        "regex": r"\.DS_Store$",
        "match": False
    },
    "Appledouble": {
        "regex": r"\._.+$",
        "match": False
    },
    "Icon": {
        "regex": r"(I|i)con(|\r)$",
        "match": False
    }
}

LOGGER = logging.getLogger(__name__)

#NEED EXCEPTION CLASS

class Repairable_Bag(bagit.Bag):

  def __init__(self, *args, **kwargs):
    super(Repairable_Bag, self).__init__(*args, **kwargs)
    self.old_dir = os.path.abspath(os.path.curdir)
    self.manifests_updated = False

    self.premis_path = os.path.join(self.path, 'premis-events.json')
    if os.path.isfile(self.premis_path):
      with open(self.premis_path, 'r') as f:
        self.premis_events = json.load(f)
    else:
      self.premis_events = []


  def add_premisevent(self, process, msg, outcome, sw_agent,
    human_agent = None):
    premis_event = {
      'Event-Date-Time': datetime.datetime.strftime(
        datetime.datetime.now(), "%Y%m%d%H%M%S%Z"),
      'Event-Type': process,
      'Event-Detail-Information': msg,
      'Event-Outcome': outcome,
      'Event-Software-Agent': sw_agent
    }
    if human_agent:
      premis_event['Event-Human-Agent']: human_agent

    self.premis_events.append(premis_event)


  def write_premisjson(self):
    with open(self.premis_path, 'w') as f:
      json.dump(self.premis_events, f)

    return True


  def check_oxum(self):
    try:
      self._validate_oxum()
    except bagit.BagValidationError:
      return False
    return True


  def write_baginfo(self):
    if self.check_oxum():
      return False

    total_bytes = 0
    total_files = 0

    for payload_file in self.payload_files():
      payload_file = os.path.join(self.path, payload_file)
      total_bytes += os.stat(payload_file).st_size
      total_files += 1

    generated_oxum = "{0}.{1}".format(total_bytes, total_files)

    if self.info["Payload-Oxum"] != generated_oxum:
      self.info["Payload-Oxum"] = generated_oxum

      self.add_premisevent(process = "Bag Info Update",
        msg = "Update 0xum from {} to {}".format(
          self.info["Payload-Oxum"], generated_oxum),
        outcome = "Pass", sw_agent = "update_bag.py")

    try:
      bagit._make_tag_file(os.path.join(self.path, "bag-info.txt"), self.info)
    except:
      LOGGER.error("Do not have permission to overwrite bag-info")

    return True


  def write_hash_manifests(self):
    if not self.manifests_updated:
      return False

    today = datetime.datetime.strftime(
      datetime.datetime.now(), "%Y%m%d%H%M%S")
    for alg in set(self.algs):
      manifest_path = os.path.join(self.path, 'manifest-{}.txt'.format(alg))
      copy_manifest_path = os.path.join(self.path, 'manifest-{}-{}.old'.format(alg, today))
      try:
        shutil.copyfile(manifest_path, copy_manifest_path)
      except:
        LOGGER.error("Do not have permission to write new manifests")
      else:
        self.add_premisevent(process = "Copy Bag Manifest",
          msg = "{} copied to {} before writing new manifest".format(
            manifest_path, copy_manifest_path),
          outcome = "Pass", sw_agent = "update_bag.py")

      try:
        with open(manifest_path, 'w') as manifest:
          for payload_file, hashes in self.entries.items():
            if payload_file.startswith("data" + os.sep):
              manifest.write("{} {}\n".format(hashes[alg], bagit._encode_filename(payload_file)))
      except:
        LOGGER.error("Do not have permission to overwrite hash manifests")
      else:
        self.add_premisevent(process = "Write Bag Manifest",
          msg = "{} written as a result of new or updated payload files".format(
            manifest_path),
          outcome = "Pass", sw_agent = "update_bag.py")

    return True


  def write_tag_manifests(self):
    for alg in set(self.algs):
      try:
        bagit._make_tagmanifest_file(alg, self.path)
      except:
        LOGGER.error("Do not have permission to overwrite tag manifests")

    return True


  def write_bag_updates(self):
    self.write_baginfo()
    self.write_hash_manifests()
    self.write_premisjson()
    self.write_tag_manifests()


  '''
  def remove_manifestentry(self):
  '''


  def payload_files_not_in_manifest(self):
    """
    find all dem new files
    """
    if self.compare_manifests_with_fs()[1]:
      for payload_file in self.compare_manifests_with_fs()[1]:
        yield payload_file


  def add_new_hashes_for_file(self, payload_file):
    """
    add new hashes for each new files
    """
    stuff = {}
    for alg in set(self.algs):
      hash, filename, size = bagit._manifest_line(payload_file, alg)
      stuff[alg] = hash

    self.entries[filename] = stuff


  def add_payload_files_not_in_manifest(self):
    """
    iterate through all dem new files
    """
    os.chdir(self.path)

    new_payload_files = list(self.payload_files_not_in_manifest())

    if new_payload_files:
      LOGGER.info("Adding the following files to manifests: {}".format(", ".join(new_payload_files)))
      self.manifests_updated = True

      for payload_file in self.payload_files_not_in_manifest():
        self.add_new_hashes_for_file(payload_file)

      self.add_premisevent(process = "Bag Payload Update",
        msg = "Added the following files to the bag payload: {}".format(
          ", ".join(new_payload_files)),
        outcome = "Pass", sw_agent = "update_bag.py")

      self.write_bag_updates()

    os.chdir(self.old_dir)


  def update_hashes(self, filename_pattern = None):
    os.chdir(self.path)

    payload_files = set(self.payload_entries().keys())

    if filename_pattern:
      regex = re.compile(filename_pattern)
      files_to_update = [x for x in payload_files if regex.search(x)]
    else:
      files_to_update = payload_files

    if files_to_update:
      LOGGER.info("Updating hashes for the following files: {}".format(", ".join(files_to_update)))
      self.manifests_updated = True

      for payload_file in files_to_update:
        self.add_new_hashes_for_file(payload_file)

      self.add_premisevent(process = "Bag Payload Hash Update",
        msg = "Changed hashes for the following files: {}".format(
          ", ".join(files_to_update)),
        outcome = "Pass", sw_agent = "update_bag.py")

      self.write_bag_updates()

    os.chdir(self.old_dir)


  def delete_payload_files_not_in_manifest(self, rules = SYSTEM_FILE_PATTERNS):
    """
    iterate through all dem new files
    """
    new_payload_files = list(self.payload_files_not_in_manifest())

    if rules:
      files_to_delete = list()
      files_not_to_delete = list()
      for payload_file in new_payload_files:
        for rulename, rule in rules.items():
          if bool(re.search(rule["regex"], payload_file)) != rule["match"]:
            files_to_delete.append(payload_file)
        if payload_file not in files_to_delete:
          files_not_to_delete.append(payload_file)
    else:
      files_to_delete = new_payload_files

    if files_not_to_delete:
      LOGGER.warning("Untracked files in payload directory do not match deletion rules: {}".format(", ".join(files_not_to_delete)))

    os.chdir(self.path)
    if files_to_delete:
      LOGGER.warning("Will delete the following files: {}".format(", ".join(files_to_delete)))
      for payload_file in files_to_delete:
        try:
          LOGGER.warning("Deleting {}".format(payload_file))
          os.remove(payload_file)
        except OSError:
          LOGGER.error("Do not have permission to delete {}".format(payload_file))
          
      self.add_premisevent(process = "Update Bag Payload",
        msg = "Deleted untracked files from the payload directory: {}".format(
          ", ".join(files_to_delete)),
        outcome = "Pass", sw_agent = "update_bag.py")

      if not self.check_oxum():
        self.write_bag_updates()

    os.chdir(self.old_dir)
