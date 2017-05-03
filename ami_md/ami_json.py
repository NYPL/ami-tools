import os
import json
import logging
import math

LOGGER = logging.getLogger(__name__)


class AMIJSONError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class ami_json:
  def __init__(self, filename=None, flat_dict = None, schema_version = "x.0.0"):
    """
    Initialize object as nested json
    """

    if filename:
      try:
        self.name = filename
        with open(filename, 'r', encoding = 'utf-8-sig') as f:
          self.dict = json.load(f)
      except:
        print("not a json file")
      else:
        self.filename = os.path.splitext(os.path.abspath(filename))[0]

    if flat_dict:
      nested_dict = {}
      if "asset.schemaVersion" not in flat_dict.items():
          flat_dict["asset.schemaVersion"] = schema_version
      for key, value in flat_dict.items():
        if value == value and  value:
          nested_dict = self.convert_dotKeyToNestedDict(
            nested_dict, key, value)

      self.dict = nested_dict
      self.coerce_strings()


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


  def write_json(self, output_directory):
    if not os.path.exists(output_directory):
      self.raise_jsonerror('output directory does not exist')
    else:
      json_directory = output_directory

    json_filename = "{0}/{1}.{2}.json".format(
      json_directory,
      self.dict['asset']['referenceFilename'],
      self.dict['technical']['extension'])

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
