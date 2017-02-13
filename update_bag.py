import argparse
import bagit
import os
import shutil
import datetime
import re

SYSTEM_FILE_PATTERNS = {
    "Thumbs.db": {
        "regex": r"[Tt]humbs\\.db$",
        "match": False
    },
    "DS_Store": {
        "regex": r"\\.DS_Store$",
        "match": False
    },
    "Appledouble": {
        "regex": r"\\._.+$",
        "match": False
    },
    "Icon": {
        "regex": r"(I|i)con(|\r)$",
        "match": False
    }
}


class Repairable_Bag(bagit.Bag):

  def __init__(self, *args, **kwargs):
    super(Repairable_Bag, self).__init__(*args, **kwargs)
    self.old_dir = os.path.abspath(os.path.curdir)

  def check_baginfo(self):
    try:
      self.validate(fast = True)
    except bagit.BagValidationError:
      return False
    return True


  def update_baginfo(self, message = None):

    today = datetime.date.strftime(datetime.date.today(), "%Y-%m-%d")

    total_bytes = 0
    total_files = 0

    for payload_file in self.payload_files():
      payload_file = os.path.join(self.path, payload_file)
      total_bytes += os.stat(payload_file).st_size
      total_files += 1

    generated_oxum = "{0}.{1}".format(total_bytes, total_files)

    if self.info["Payload-Oxum"] != generated_oxum:
      self.info["Payload-Oxum-Before-{}".format(today)] = self.info["Payload-Oxum"]
      self.info["Most-Recent-Update-Date"] = today
      self.info["Payload-Oxum"] = generated_oxum

    if message:
      self.info["Update-Message-{}".format(today)] = message
      self.info["Most-Recent-Update-Date"] = today


    try:
      bagit._make_tag_file(os.path.join(self.path, "bag-info.txt"), self.info)
    except:
      print("Do not have permission to overwrite bag-info")
      return False

    for alg in set(self.algs):
      bagit._make_tagmanifest_file(alg, self.path)

    return True

  '''
  def remove_manifestentry(self):

  def remove_payload(self):
  '''

  def payload_files_not_in_manifest(self):
    """
    find all dem new files
    """
    if self.compare_manifests_with_fs()[1]:
      for payload_file in self.compare_manifests_with_fs()[1]:
         yield payload_file

  def add_payload_files_not_in_manifest(self):
    """
    iterate through all dem new files
    """
    os.chdir(self.path)

    new_payload_files = list(self.payload_files_not_in_manifest())
    for payload_file in self.payload_files_not_in_manifest():
      #print payload_file
      self.add_payload_file_to_manifest(payload_file)

    self.update_baginfo()
    self.copy_manifest_files()
    self.rewrite_manifest_files()

    os.chdir(self.old_dir)


  def add_payload_file_to_manifest(self, payload_file):
    """
    add new hashes for each new files
    """
    stuff = {}
    for alg in set(self.algs):
      hash, filename, size = bagit._manifest_line(payload_file, alg)
      stuff[alg] = hash

    self.entries[filename] = stuff


  def delete_payload_files_not_in_manifest(self, rules = None):
    """
    iterate through all dem new files
    """
    new_payload_files = list(self.payload_files_not_in_manifest())

    if rules:
      files_to_delete = list()
      for payload_file in new_payload_files:
        for rulename, rule in rules.items():
          if bool(re.search(rule["regex"], payload_file)) != rule["match"]:
            files_to_delete.append(payload_file)
    else:
      files_to_delete = new_payload_files

    os.chdir(self.path)

    for payload_file in files_to_delete:
      #print payload_file
      try:
        os.remove(payload_file)
        #logging.info("Deleted {0}".format(path))
      except OSError:

        "eh"
        #logging.error("Could not delete {0}".format(path))

    os.chdir(self.old_dir)

    self.update_baginfo()
    self.rewrite_manifest_files()


  def copy_manifest_files(self):
    today = datetime.date.strftime(datetime.date.today(), "%Y-%m-%d")
    for alg in self.algs:
      shutil.copyfile('manifest-{}.txt'.format(alg),
        'manifest-{}-{}.txt.old'.format(alg, today))


  def rewrite_manifest_files(self):
    for alg in set(self.algs):
      with open('manifest-%s.txt' % alg, 'w') as manifest:
        for payload_file, hashes in self.entries.items():
          if payload_file.startswith("data" + os.sep):
            manifest.write("%s  %s\n" % (hashes[alg], bagit._encode_filename(payload_file)))

    for alg in set(self.algs):
      bagit._make_tagmanifest_file(alg, self.path)
