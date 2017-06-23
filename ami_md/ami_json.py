import os
import json
import re
import logging
from pandas.tslib import Timestamp
import numpy as np
from pymediainfo import MediaInfo


FULL_TECHFN_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(pm|em|sc)$"
STUB_TECHFN_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(pm|em|sc)"
FULL_REFFN_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(pm|em|sc)\.(mov|wav|mkv|dv)$"

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
      self.filename = os.path.splitext(os.path.basename(filepath))[0]
      if load:
        try:
          with open(filepath, 'r', encoding = 'utf-8-sig') as f:
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

      if media_filepath and os.path.isfile(media_filepath):
        self.media_filepath = media_filepath
      else:
        raise_jsonerror("There is no media file found at {}".format(media_filepath))


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


  def update_mediainfo(self):
    file_techmd = MediaInfo.parse(self.media_filepath)

    for track in file_techmd.tracks:
      if track.track_type == "General":
        self.dict["technical"]["filename"] = track.file_name
        self.dict["technical"]["extension"] = track.file_extension
        self.dict["technical"]["fileFormat"] = track.format
        self.dict["technical"]["fileSize"]["measure"] = track.file_size
        self.dict["technical"]["dateCreated"] = track.encoded_date.split()[0].replace(":", "-")
        self.dict["technical"]["durationHuman"] = track.other_duration[-1]
        if "durationMilli" not in self.dict["technical"].keys():
          self.dict["technical"]["durationMilli"] = {}
        self.dict["technical"]["durationMilli"]["measure"] = track.duration
        self.dict["technical"]["durationMilli"]["unit"] = "ms"
        self.dict["technical"]["audioCodec"] = track.audio_codecs
        if track.codecs_video:
          self.dict["technical"]["videoCodec"] = track.codecs_video


  def check_techfn(self):
    if not re.match(FULL_TECHFN_RE, self.dict["technical"]["filename"]):
      self.raise_jsonerror("Value for technical.filename does not meet expectations: {}"
        .format(self.dict["technical"]["filename"]))

    return True


  def repair_techfn(self, techfn = None):
    if techfn:
      self.dict["technical"]["filename"] = techfn
    else:
      if not re.match(FULL_TECHFN_RE, self.dict["technical"]["filename"]):
        correct_techfn = re.match(STUB_TECHFN_RE, self.dict["technical"]["filename"])
        if correct_techfn:
          self.dict["technical"]["filename"] = correct_techfn[0]
          LOGGER.info("{} technical.filename updated to: {}".format(self.filename, self.dict["technical"]["filename"]))
        else:
          raise_jsonerror("Correct technical.filename cannot be determined from current value")


  def check_reffn(self):
    if not re.match(FULL_REFFN_RE, self.dict["asset"]["referenceFilename"]):
      self.raise_jsonerror("Value for asset.referenceFilename does not meet expectations: {}"
        .format(self.dict["asset"]["referenceFilename"]))

    return True


  def repair_reffn(self, reffn = None):
    if reffn:
      self.dict["asset"]["referenceFilename"] = reffn
    else:
      if not re.match(FULL_REFFN_RE, self.dict["asset"]["referenceFilename"]):
        if self.check_techfn():
          original_value = self.dict["asset"]["referenceFilename"]
          replacement_value = self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]
          self.dict["asset"]["referenceFilename"] = replacement_value

          if self.check_reffn():
            LOGGER.info("{} asset.referenceFilename updated to: {}".format(self.filename, self.dict["asset"]["referenceFilename"]))
          else:
            self.dict["asset"]["referenceFilename"] = original_value
            raise_jsonerror("Correct asset.referenceFilename cannot be created from technical.filename and technical.extension.")


  def compare_techfn_reffn(self):
    if self.dict["asset"]["referenceFilename"] != self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]:
      self.raise_jsonerror("Value for asset.referenceFilename should equal technical.filename.technical.extension: {} != {}.{}"
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
