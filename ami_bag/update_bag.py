import os, re, json, shutil, logging
import datetime
import sys

import bagit


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

  def __init__(self, repairer = None, dryrun = False, *args, **kwargs):
    super(Repairable_Bag, self).__init__(*args, **kwargs)
    self.old_dir = os.path.abspath(os.path.curdir)
    self.manifests_updated = False
    self.dryrun = dryrun

    if repairer:
      self.repairer = repairer
    else:
      self.repairer = None

    self.premis_path = os.path.join(self.path, 'premis-events.json')
    if os.path.isfile(self.premis_path):
      with open(self.premis_path, 'r') as f:
        self.premis_events = json.load(f)
    else:
      self.premis_events = []


  def add_premisevent(self, process, msg, outcome, sw_agent, date = None,
    human_agent = None):
    if not date:
      date = datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d%H%M%S.%f%Z")
    premis_event = {
      'Event-Date-Time': date,
      'Event-Type': process,
      'Event-Detail-Information': msg,
      'Event-Outcome': outcome,
      'Event-Software-Agent': sw_agent
    }

    if human_agent:
      premis_event['Event-Human-Agent'] = human_agent
    elif self.repairer:
      premis_event['Event-Human-Agent'] = self.repairer

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

      self.add_premisevent(process = "Bag Info Update",
        msg = "Update 0xum from {} to {}".format(
          self.info["Payload-Oxum"], generated_oxum),
        outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)
      self.info["Payload-Oxum"] = generated_oxum

      try:
        bagit._make_tag_file(os.path.join(self.path, "bag-info.txt"), self.info)
      except:
        LOGGER.error("Do not have permission to overwrite bag-info")
      else:
        LOGGER.info("bag-info.txt written")

    return True


  def write_hash_manifests(self):
    if not self.manifests_updated:
      return False

    today = datetime.datetime.strftime(
      datetime.datetime.now(), "%Y%m%d%H%M%S")
    for alg in set(self.algorithms):
      manifest_path = os.path.join(self.path, 'manifest-{}.txt'.format(alg))
      copy_manifest_path = os.path.join(self.path, 'manifest-{}-{}.old'.format(alg, today))
      try:
        shutil.copyfile(manifest_path, copy_manifest_path)
      except:
        LOGGER.error("Do not have permission to write new manifests")
      else:
        self.add_premisevent(process = "Copy Bag Manifest",
          msg = "{} copied to {} before writing new manifest".format(
            os.path.basename(manifest_path),
            os.path.basename(copy_manifest_path)),
          outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)

      try:
        with open(manifest_path, 'w') as manifest:
          for payload_file, hashes in self.entries.items():
            if payload_file.startswith("data" + os.sep):
              manifest.write("{} {}\n".format(hashes[alg], bagit._encode_filename(payload_file)))
      except:
        LOGGER.error("Do not have permission to overwrite hash manifests")
      else:
        LOGGER.info("{} written".format(manifest_path))
        self.add_premisevent(process = "Write Bag Manifest",
          msg = "{} written as a result of new or updated payload files".format(
            os.path.basename(manifest_path)),
          outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)

    return True


  def write_tag_manifests(self):
    for alg in set(self.algorithms):
      try:
        bagit._make_tagmanifest_file(alg, self.path)
      except:
        LOGGER.error("Do not have permission to overwrite tag manifests")

    return True


  def write_bag_updates(self):
    if not self.dryrun:
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
    new_hashes = {}
    results = bagit.generate_manifest_lines(payload_file, self.algorithms)

    for line in results:
        new_hashes[line[0]] = line[1]

    if payload_file not in self.entries.keys():
      self.entries[payload_file] = new_hashes
      return True
    elif self.entries[payload_file] != new_hashes:
      self.entries[payload_file] = new_hashes
      return True
    else:
      return False


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
        outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)

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
      LOGGER.info("Potentially updating hashes for the following files: {}".format(", ".join(files_to_update)))

      for payload_file in files_to_update:
        updated_files = []
        if self.add_new_hashes_for_file(payload_file):
          self.manifests_updated = True
          updated_files.append(payload_file)

      if self.manifests_updated:
        self.add_premisevent(process = "Bag Payload Hash Update",
          msg = "Changed hashes for the following files: {}".format(
            ", ".join([os.path.basename(x) for x in updated_files])),
          outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)

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
          ", ".join([os.path.basename(x) for x in files_to_delete])),
        outcome = "Pass", sw_agent = sys._getframe().f_code.co_name)

      if not self.check_oxum():
        self.write_bag_updates()

    os.chdir(self.old_dir)
