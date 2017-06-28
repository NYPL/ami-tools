import os
import json
import re
import logging
from pandas.tslib import Timestamp
import numpy as np
from pymediainfo import MediaInfo


FULL_TECHFN_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(pm|em|sc)$"
STUB_TECHFN_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(pm|em|sc)"
FULL_REFFN_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(pm|em|sc)\.(mov|wav|mkv|dv|mp4)$"

AUDIOFIELDS = ["filename", "extension", "fileFormat",
  "fileSize", "dateCreated", "durationHuman", "durationMilli",
  "audioCodec"]
VIDEOFIELDS = ["filename", "extension", "fileFormat",
  "fileSize", "dateCreated", "durationHuman", "durationMilli",
  "audioCodec", "videoCodec"]

LOGGER = logging.getLogger(__name__)


class AMIJSONError(Exception):
  def __init__(self, message):
    self.message = message
  def __str__(self):
    return repr(self.message)


class ami_json:
  def __init__(self, filepath = None, load = True, flat_dict = None,
    schema_version = "x.0.0", media_filepath = None):
    """
    Initialize object as nested json
    """

    if filepath:
      self.path = filepath
      self.filename = os.path.basename(filepath)
      if load:
        try:
          with open(self.path, 'r', encoding = 'utf-8-sig') as f:
            self.dict = json.load(f)
        except:
          print("not a json file")

    if flat_dict:
      self.filename = os.path.splitext(flat_dict["asset.referenceFilename"])[0] + ".json"
      nested_dict = {}
      if "asset.schemaVersion" not in flat_dict.items():
          flat_dict["asset.schemaVersion"] = schema_version
      for key, value in flat_dict.items():
        if value:
          if type(value) == Timestamp:
            value = value.strftime('%Y-%m-%d')
          if isinstance(value, np.generic):
            value = np.asscalar(value)
          nested_dict = self.convert_dotKeyToNestedDict(
            nested_dict, key, value)

      self.dict = nested_dict
      self.coerce_strings()

    if media_filepath:
      self.set_mediafilepath(media_filepath)


  def set_mediafilepath(self, media_filepath = None):
    if not media_filepath:
      if hasattr(self, "path"):
        try:
          self.check_reffn()
        except:
          try:
            self.check_techfn()
          except:
            raise_jsonerror("Cannot determine described media file based on filename metdata")
          else:
            media_filename = self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]
        else:
          media_filename = self.dict["asset"]["referenceFilename"]

        media_filepath = os.path.join(os.path.split(self.path)[0], media_filename)
      else:
        raise_jsonerror("Cannot determine described media file location with json file location")

    if os.path.isfile(media_filepath):
      self.media_filepath = media_filepath
    else:
      self.raise_jsonerror("There is no media file found at {}".format(media_filepath))



  def convert_dotKeyToNestedDict(self, tree, key, value):
    """
    Recursive method that takes a dot-delimited header and returns a
    nested dictionary.

    Keyword arguments:
    key -- dot-delimited header string
    value -- value associated with header
    """

    t = tree
    if "." in key:
      key, rest = key.split(".", 1)
      if key not in tree:
        t[key] = {}
      self.convert_dotKeyToNestedDict(t[key], rest, value)
    else:
      t[key] = value

    return t


  def convert_nestedDictToDotKey(self, tree, separator = ".", prefix = ""):
    """
    Recursive method that takes a dot-delimited header and returns a
    nested dictionary.

    Keyword arguments:
    key -- dot-delimited header string
    value -- value associated with header
    """

    new_tree = {}

    for key, value in tree.items():
      key = prefix + key
      if isinstance(value, dict):
        new_tree.update(self.convert_nestedDictToDotKey(value, separator, key + separator))
      else:
        new_tree[key] = value

    return new_tree


  def coerce_strings(self):
    for key, item in self.dict["bibliographic"].items():
      self.dict["bibliographic"][key] = str(item).split('.')[0]

    for key, item in self.dict["digitizer"]["organization"]["address"].items():
      self.dict["digitizer"]["organization"]["address"][key] = str(item).split('.')[0]


  def validate_json(self):
    """
    Check the metadata values for common errors.
    """
    valid = True

    LOGGER.info("Checking: {}".format(os.path.basename(self.filename)))
    #Check for a sheet that should have preservation metadata data
    try:
      self.check_techfn()
    except AMIJSONError as e:
      LOGGER.error("Error in JSON metadata: {0}".format(e.message))
      valid = False

    try:
      self.check_reffn()
    except AMIJSONError as e:
      LOGGER.error("Error in JSON metadata: {0}".format(e.message))
      valid = False

    try:
      self.compare_techfn_reffn()
    except AMIJSONError as e:
      LOGGER.error("Error in JSON metadata: {0}".format(e.message))
      valid = False

    try:
      self.check_techmd_fields()
    except AMIJSONError as e:
      LOGGER.error("Error in JSON metadata: {0}".format(e.message))
      valid = False

    try:
      self.check_techmd_values()
    except AMIJSONError as e:
      LOGGER.error("Error in JSON metadata: {0}".format(e.message))
      valid = False

    return valid


  def check_techmd_fields(self):
    self.techmd_field_valid = False
    found_fields = set(list(self.dict["technical"].keys()))

    format_type = self.dict["source"]["object"]["type"][0:5]
    if format_type == "audio":
      expected_fields = AUDIOFIELDS
    elif format_type == "video":
      expected_fields = VIDEOFIELDS

    if not found_fields >= set(expected_fields):
      self.raise_jsonerror("Metadata is missing the following fields: {}".format(
        expected_fields - found_fields))

    self.valid_techmd_fields = True

    return True


  def set_techmd(self):
    if not hasattr(self, 'media_filepath'):
      self.set_mediafilepath()

    file_techmd = MediaInfo.parse(self.media_filepath)

    for track in file_techmd.tracks:
      if track.track_type == "General":
        self.techmd = track


  def check_techmd_values(self):
    if not hasattr(self, 'valid_techmd_fields'):
      self.check_techmd_fields()

    if not hasattr(self, 'techmd'):
      self.set_techmd()

    techmd_mapping = []

    for item in techmd_mapping:
      try:
        self.check_md_value(item[0], item[1])
      except AMIJSONError as e:
        self.raise_jsonerror(e)


  def check_md_value(self, field, expected_value, separator = '.'):
    keys = field.split(separator)
    md_value = self.dict
    for key in keys:
      md_value = md_value[key]

    if md_value != expected_value:
      self.raise_jsonerror("Incorrect value for {0}. Expected: {1}, Found: {2}".format(
        field, expected_value, md_value
      ))

    return True


  def repair_techmd(self):
    if not hasattr(self, 'techmd'):
      self.set_techmd()

    LOGGER.info("Rewriting technical md for {}".format(os.path.basename(self.filename)))
    self.dict["technical"]["filename"] = self.techmd.file_name
    self.dict["technical"]["extension"] = self.techmd.file_extension
    self.dict["technical"]["fileFormat"] = self.techmd.format

    if "fileSize" not in self.dict["technical"].keys():
      self.dict["technical"]["fileSize"] = {}
    self.dict["technical"]["fileSize"]["measure"] = self.techmd.file_size
    self.dict["technical"]["fileSize"]["unit"] = "B"

    #retain original dates
    if not "dateCreated" in self.dict["technical"].keys():
      if self.techmd.encoded_date:
        self.dict["technical"]["dateCreated"] = self.techmd.encoded_date.split()[0].replace(":", "-")
      elif self.techmd.recorded_date:
        self.dict["technical"]["dateCreated"] = self.techmd.recorded_date.split()[0].replace(":", "-")
      elif self.techmd.file_last_modification_date__local:
        self.dict["technical"]["dateCreated"] = self.techmd.file_last_modification_date__local.split()[0].replace(":", "-")

    self.dict["technical"]["durationHuman"] = self.techmd.other_duration[-3]
    if "durationMilli" not in self.dict["technical"].keys():
      self.dict["technical"]["durationMilli"] = {}
    self.dict["technical"]["durationMilli"]["measure"] = self.techmd.duration
    self.dict["technical"]["durationMilli"]["unit"] = "ms"

    self.dict["technical"]["audioCodec"] = self.techmd.audio_format_list
    if self.techmd.codecs_video:
      self.dict["technical"]["videoCodec"] = self.techmd.video_format_list


  def check_techfn(self):
    if not "filename" in self.dict["technical"].keys():
      self.raise_jsonerror("Key missing for technical.filename")

    if not re.match(FULL_TECHFN_RE, self.dict["technical"]["filename"]):
      self.raise_jsonerror("Value for technical.filename does not meet expectations: {}"
        .format(self.dict["technical"]["filename"]))

    return True


  def repair_techfn(self):
    correct_techfn = re.match(STUB_TECHFN_RE, self.dict["technical"]["filename"])

    if correct_techfn:
      self.dict["technical"]["filename"] = correct_techfn[0]
      LOGGER.info("{} technical.filename updated to: {}".format(self.filename, self.dict["technical"]["filename"]))
      return True

    else:
      LOGGER.warning("Valid technical.filename could not be extracted from {}".format(original_value))
      return False


  def check_reffn(self):
    if not "referenceFilename" in self.dict["asset"].keys():
      self.raise_jsonerror("Key missing for asset.referenceFilename")

    if not re.match(FULL_REFFN_RE, self.dict["asset"]["referenceFilename"]):
      self.raise_jsonerror("Value for asset.referenceFilename does not meet expectations: {}"
        .format(self.dict["asset"]["referenceFilename"]))

    return True


  def repair_reffn(self):
    try:
      self.check_techfn()

    except AMIJSONError as e:
      LOGGER.warning("Valid asset.referenceFilename cannot be created from technical fields: {}".format(
        self.dict["technical"]["filename"], self.dict["technical"]["extension"]))
      return False

    else:
      replacement_value = self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]
      self.dict["asset"]["referenceFilename"] = replacement_value
      LOGGER.info("{} asset.referenceFilename updated to: {}".format(self.filename, self.dict["asset"]["referenceFilename"]))
      return True


  def compare_techfn_reffn(self):
    if self.dict["asset"]["referenceFilename"] != self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]:
      self.raise_jsonerror("Value for asset.referenceFilename should equal technical.filename + technical.extension: {} != {}.{}"
        .format(self.dict["asset"]["referenceFilename"],
          self.dict["technical"]["filename"], self.dict["technical"]["extension"]))

    return True


  def write_json(self, output_directory):
    if not os.path.exists(output_directory):
      self.raise_jsonerror('output directory does not exist')
    else:
      json_directory = output_directory

    json_filename = "{0}/{1}.json".format(
      json_directory,
      self.dict['technical']['filename'])

    with open(json_filename, 'w') as f:
      json.dump(self.dict, f)
      LOGGER.info("{} written".format(json_filename))


  def raise_jsonerror(self, msg):
    """
    lazy error reporting
    """

    raise AMIJSONError(msg)
    logging.error(msg + '\n')
    return False
