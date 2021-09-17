import os, json, re, logging

# data manipulation
import numpy as np
import pandas as pd

# ami modules
import ami_files.ami_file as ami_file
import ami_files.ami_file_constants as ami_file_constants
import ami_md.ami_md_constants as ami_md_constants


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
          self.raise_jsonerror('Could not load {}. Check that it is valid JSON.'.format(self.filename))
        else:
          self.set_mediaformattype()

    if flat_dict:
      self.filename = os.path.splitext(flat_dict["asset.referenceFilename"])[0] + ".json"
      nested_dict = {}
      if "asset.schemaVersion" not in flat_dict.items():
          flat_dict["asset.schemaVersion"] = schema_version
      for key, value in flat_dict.items():
        if value:
          if pd.isnull(value):
            continue
          if type(value) == pd.Timestamp:
            value = value.strftime('%Y-%m-%d')
          if isinstance(value, np.generic):
            value = np.asscalar(value)
          nested_dict = convert_dotKeyToNestedDict(
            nested_dict, key, value)

      self.dict = nested_dict
      self.set_mediaformattype()
      self.coerce_strings()

    if media_filepath:
      self.set_mediafilepath(media_filepath)



  def set_mediaformattype(self):
    try:
      hasattr(self, 'dict')
    except AttributeError:
      self.raise_jsonerror('Cannot set format type, metadata dictionary not loaded.')

    self.media_format_type = self.dict["source"]["object"]["type"][0:5]



  def set_mediafilepath(self, media_filepath = None):
    if not media_filepath:
      LOGGER.info('Attempting to locate media file based on JSON file location.')
      if hasattr(self, "path"):
        try:
          self.check_reffn()
        except:
          try:
            self.check_techfn()
          except:
            self.raise_jsonerror("Cannot determine described media file based on filename metdata")
          else:
            media_filename = self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]
        else:
          media_filename = self.dict["asset"]["referenceFilename"]

        media_filepath = os.path.join(os.path.split(self.path)[0], media_filename)
      else:
        self.raise_jsonerror("Cannot determine described media file location with json file location")

    if os.path.isfile(media_filepath):
      self.media_filepath = media_filepath
    else:
      self.raise_jsonerror("There is no media file found at {}".format(media_filepath))


  def coerce_strings(self):
    for key, item in self.dict["bibliographic"].items():
      self.dict["bibliographic"][key] = str(item).split('.')[0]

    try:
      for key, item in self.dict["digitizer"]["organization"]["address"].items():
        self.dict["digitizer"]["organization"]["address"][key] = str(item).split('.')[0]
    except:
      return


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
      LOGGER.warning("JSON metadata out of spec: {0}".format(e.message))
      valid = False

    try:
      self.check_reffn()
    except AMIJSONError as e:
      LOGGER.warning("JSON metadata out of spec: {0}".format(e.message))
      valid = False

    try:
      self.compare_techfn_reffn()
    except AMIJSONError as e:
      LOGGER.warning("JSON metadata out of spec: {0}".format(e.message))
      valid = False

    try:
      self.check_techmd_fields()
    except AMIJSONError as e:
      LOGGER.error("JSON metadata out of spec: {0}".format(e.message))
      valid = False

    if hasattr(self, 'media_filepath'):
      try:
        self.compare_techfn_media_filename()
      except AMIJSONError as e:
        LOGGER.error("JSON metadata out of spec: {0}".format(e.message))
        valid = False

      try:
        self.check_techmd_values()
      except AMIJSONError as e:
        LOGGER.warning("JSON metadata out of spec: {0}".format(e.message))
        valid = False
    else:
      LOGGER.warning('Cannot check technical metadata values against media file without location of the described media file.')

    return valid


  def check_techmd_fields(self):
    self.valid_techmd_fields = False
    found_fields = set(list(self.dict["technical"].keys()))

    if self.media_format_type == "audio":
      expected_fields = set(ami_md_constants.JSON_AUDIOFIELDS)
    elif self.media_format_type == "video":
      expected_fields = set(ami_md_constants.JSON_VIDEOFIELDS)

    if not found_fields >= expected_fields:
      self.raise_jsonerror("Metadata is missing the following fields: {}".format(
        expected_fields - found_fields))

    self.valid_techmd_fields = True

    return True


  def set_media_file(self, mi = True):
    if not hasattr(self, 'media_filepath'):
      self.set_mediafilepath()

    self.media_file = ami_file.ami_file(self.media_filepath, mi)


  def check_techmd_values(self):
    if not hasattr(self, 'valid_techmd_fields'):
      self.check_techmd_fields()

    if not hasattr(self, 'media_file'):
      self.set_media_file()

    if self.media_format_type == "audio":
      field_mapping = ami_md_constants.JSON_TO_AUDIO_FILE_MAPPING
    elif self.media_format_type == "video":
      field_mapping = ami_md_constants.JSON_TO_VIDEO_FILE_MAPPING

    errors = []
    for key, value in field_mapping.items():
      try:
        self.check_md_value(key, value)
      except AMIJSONError as e:
        errors.append(e.message)

    if errors:
      self.raise_jsonerror(' '.join(errors))

    return True


  def check_md_value(self, field, mapped_field, separator = '.'):
    try:
      file_value = getattr(self.media_file, mapped_field)
    except AttributeError:
      self.raise_jsonerror("File does not have expected attribute: {}".format(
        mapped_field
      ))

    md_value = self.dict["technical"]
    if separator in field:
      field_parts = field.split(separator)
      for part in field_parts:
        md_value = md_value[part]
    else:
      md_value = md_value[field]

    if md_value != file_value:
      if field == 'dateCreated':
        LOGGER.warning('{0} in JSON and from file disagree. JSON: {1}, From file: {2}.'.format(
          field, md_value, file_value
        ))
      elif field == 'audioCodec':
        if md_value == 'AAC' and file_value == 'AAC LC':
          pass
      else:
        self.raise_jsonerror("Incorrect value for {0}. Expected: {1}, Found: {2}.".format(
          field, md_value, file_value
        ))

    return True


  def repair_techmd(self):
    if not hasattr(self, 'media_file'):
      self.set_media_file()

    LOGGER.info("Rewriting technical md for {}".format(os.path.basename(self.filename)))
    self.dict["technical"]["filename"] = self.media_file.base_filename
    self.dict["technical"]["extension"] = self.media_file.extension
    self.dict["technical"]["fileFormat"] = self.media_file.format

    if "fileSize" not in self.dict["technical"].keys():
      self.dict["technical"]["fileSize"] = {}
    self.dict["technical"]["fileSize"]["measure"] = self.media_file.size
    self.dict["technical"]["fileSize"]["unit"] = "B"

    if not "dateCreated" in self.dict["technical"].keys():
      self.dict["technical"]["dateCreated"] = self.media_file.date_created
    
    #self.dict["technical"]["dateCreated"] = self.media_file.date_created  

    self.dict["technical"]["durationHuman"] = self.media_file.duration_human
    if "durationMilli" not in self.dict["technical"].keys():
      self.dict["technical"]["durationMilli"] = {}
    self.dict["technical"]["durationMilli"]["measure"] = self.media_file.duration_milli
    self.dict["technical"]["durationMilli"]["unit"] = "ms"

    self.dict["technical"]["audioCodec"] = self.media_file.audio_codec
    if self.media_file.type == "video":
      self.dict["technical"]["videoCodec"] = self.media_file.video_codec


  def strip_techmd(self):
    allowed_keys = ["filename", "extension", "fileFormat", "fileSize", "dateCreated", "durationHuman", "durationMilli", "audioCodec", "videoCodec"]
    keys_to_strip = []
    for key in self.dict["technical"].keys():
      if key not in allowed_keys:
        keys_to_strip.append(key)

    for key in keys_to_strip:
      self.dict["technical"].pop(key)


  def check_techfn(self):
    if not "filename" in self.dict["technical"].keys():
      self.raise_jsonerror("Key missing for technical.filename")

    if not re.match(ami_file_constants.FN_NOEXT_RE, self.dict["technical"]["filename"]):
      self.raise_jsonerror("Value for technical.filename does not meet expectations: {}"
        .format(self.dict["technical"]["filename"]))

    return True


  def repair_techfn(self):
    correct_techfn = re.match(ami_file_constants.STUB_FN_NOEXT_RE, self.dict["technical"]["filename"])

    if correct_techfn:
      if hasattr(self, 'media_filepath'):
        try:
          self.compare_techfn_media_filename()
        except:
          LOGGER.error('Extracted technical filename does not match provide media filename.')
          return False
      try:
        self.compare_techfn_reffn()
      except:
        LOGGER.warning('Extracted technical filename does not match referenceFilename value.')
      
      self.dict["technical"]["filename"] = correct_techfn[0]
      # always prefer lowercase exts
      self.dict["technical"]["extension"] = self.dict["technical"]["extension"].lower()
      LOGGER.info("{} technical.filename updated to: {}".format(
        self.filename, self.dict["technical"]["filename"]))
      return True

    else:
      LOGGER.error("Valid technical.filename could not be extracted from {}".format(
        self.dict["technical"]["filename"]))
      return False


  def check_reffn(self):
    if not "referenceFilename" in self.dict["asset"].keys():
      self.raise_jsonerror("Key missing for asset.referenceFilename")

    if not re.match(ami_file_constants.FN_RE, self.dict["asset"]["referenceFilename"]):
      self.raise_jsonerror("Value for asset.referenceFilename does not meet expectations: {}"
        .format(self.dict["asset"]["referenceFilename"]))

    return True


  def repair_reffn(self):
    try:
      self.check_techfn()

    except AMIJSONError as e:
      LOGGER.error("Valid asset.referenceFilename cannot be created from technical fields: {}, {}".format(
        self.dict["technical"]["filename"], self.dict["technical"]["extension"]))
      return False

    else:
      replacement_value = self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]
      self.dict["asset"]["referenceFilename"] = replacement_value
      LOGGER.info("{} asset.referenceFilename updated to: {}".format(self.filename, self.dict["asset"]["referenceFilename"]))
      return True


  def compare_techfn_reffn(self):
    if not ("filename" in self.dict["technical"].keys() and
      "extension" in self.dict["technical"].keys() and
      "referenceFilename" in self.dict["asset"].keys()):
      self.raise_jsonerror("Key or keys related to filenames missing")

    if self.dict["asset"]["referenceFilename"] != self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]:
      self.raise_jsonerror("Value for asset.referenceFilename should equal technical.filename + technical.extension: {} != {}.{}"
        .format(self.dict["asset"]["referenceFilename"],
          self.dict["technical"]["filename"], self.dict["technical"]["extension"]))

    return True


  def compare_techfn_media_filename(self):
    expected_media_filename = self.dict["technical"]["filename"] + '.' + self.dict["technical"]["extension"]
    provided_media_filename = os.path.basename(self.media_filepath)

    if expected_media_filename != provided_media_filename:
      self.raise_jsonerror("Value for technical.filename + technical.extension should equal media filename: {} != {}"
        .format(expected_media_filename, provided_media_filename))

    return True


  def write_json(self, output_directory, indent = None):
    if not os.path.exists(output_directory):
      self.raise_jsonerror('output directory does not exist')
    else:
      json_directory = output_directory

    if ('technical' in self.dict.keys() and
      'filename' in self.dict['technical'].keys()):
      filename = self.dict['technical']['filename']
    elif ('asset' in self.dict.keys() and
      'referenceFilename' in self.dict['asset'].keys()):
      filename = self.dict['asset']['referenceFilename'].split('.')[0]
    else:
      self.raise_jsonerror('Metadata requires asset.referenceFilename or technical.filename to be saved.')

    json_filename = "{0}/{1}.json".format(
      json_directory,
      filename)

    with open(json_filename, 'w') as f:
      try:
        json.dump(self.dict, f, indent = indent)
        LOGGER.info("{} written".format(json_filename))
      except:
        LOGGER.error("{} could not be written".format(json_filename))


  def raise_jsonerror(self, msg):
    """
    lazy error reporting
    """

    logging.error(msg + '\n')
    raise AMIJSONError(msg)


def convert_dotKeyToNestedDict(tree, key, value):
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
    convert_dotKeyToNestedDict(t[key], rest, value)
  else:
    t[key] = value

  return t


def convert_nestedDictToDotKey(tree, separator = ".", prefix = ""):
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
      new_tree.update(convert_nestedDictToDotKey(value, separator, key + separator))
    else:
      new_tree[key] = value

  return new_tree
