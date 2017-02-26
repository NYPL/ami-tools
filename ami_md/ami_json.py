import json


class AMIExcelError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class ami_json:
  def __init__(self, filename=None, flat_dict = None):
    """
    Initialize object as nested json
    """

    if filename:
      try:
        self.name = filename
        with open(filename, 'r') as f:
          self.dict = json.load(f)
      except:
        print("not a json file")
      else:
        self.filename = os.path.splitext(os.path.abspath(filename))[0]
    
    if flat_dict:
      nested_dict = {}
      for key, value in flat_dict.items():
        nested_dict = self.convert_dotKeyToNestedDict(
          nested_dict, key, value)

      self.dict = nested_dict


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
