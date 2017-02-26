import os, re, datetime
# handling excel
import xlrd
from xlrd import xldate
from openpyxl import load_workbook
# data manipulation and output
import pandas as pd
import numpy as np
import csv, json

import ami_md.ami_md_constants as ami_md_constants
import ami_md.ami_json as ami_json



class AMIExcelError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)


class ami_excel:
  def __init__(self, filename=None):
    """
    Initialize object as excel workbook
    """
    self.name = filename
    self.wb = None
    if os.path.exists(filename):
      try:
        self.wb = xlrd.open_workbook(filename)
      except:
        print("not an excel file")
      else:
        self.set_amiSheetNames()
        self.filename = os.path.splitext(os.path.abspath(filename))[0]
    else:
      print("not a file")


  def validate_workbook(self):
    """
    Check the preservation sheet against expectations of Media Ingest.
    """

    valid = True

    #Check for a sheet that should have preservation metadata data
    try:
      self.check_presSheetExists()
    except AMIExcelError as e:
      print("Error in workbook sheets: ", e.value)
      valid = False

    #Check that preservation sheet contains required headers
    for i in range(0, 3):
      try:
        expected = set([item[i] for item in ami_md_constants.MEDIAINGEST_EXPECTED_HEADERS if item[i]])
        found = self.get_headerRow(self.pres_sheetname, i)
        self.check_headerRow(expected, found)
      except AMIExcelError as e:
        print("Error in preservation header row {}: {}"
          .format(i + 1, e.value))
        valid = False

    #Check that preservation sheet headers have the correct heirarchy
    try:
      header_entries = set(self.get_headerEntries(self.pres_sheetname))
      self.check_headerEntries(set(ami_md_constants.MEDIAINGEST_EXPECTED_HEADERS), header_entries)
    except AMIExcelError as e:
      print("Error in header entries: ", e.value)
      valid = False

    #Check that the preservation sheet does not contain equations
    try:
      self.check_noequations(self.pres_sheetname)
    except AMIExcelError as e:
      print("Error in cell values: ", e.value)
      valid = False

    return valid


  def set_amiSheetNames(self):
    """
    Identifies sheets that should contain data about preservation files,
    edit master files, and untransferred objects.
    """

    self.pres_sheetname = None
    self.edit_sheetname = None
    self.notransfer_sheetname = None

    for sheet in self.wb.sheet_names():
      sheet_lower = sheet.lower()
      #Check if two sheets get identfied by regex below?
      if re.match("(original|preservation|file|full|archive)",
        sheet_lower):
        self.pres_sheetname = sheet
      elif re.match("edit", sheet_lower):
        self.edit_sheetname = sheet
      elif re.match("not transferred", sheet_lower):
        self.notransfer_sheetname = sheet



  def check_presSheetExists(self):
    """
    Checks if a preservation sheet has been identified by
    set_amiSheetNames()
    """

    if not self.pres_sheetname:
      self.raise_excelerror("Required sheet for preservation files" +
        "could not be found in workbook.")

    return True


  def get_headerRow(self, sheetname, row):
    """
    Return normalized values from a single row of headers on a
    specified sheet. Newline characters are retained.

    Keyword arguments:
    sheetname -- name of the sheet to extract from (self.pres_sheetname
    or self.edit_sheetname)
    row -- index of the row to extract from (0-2)
    """

    sheet = self.wb.sheet_by_name(sheetname)
    headers = []

    for i in range(0, sheet.ncols):
      value = str(sheet.cell(row, i).value)

      if value:
        headers.append(value)

    return headers


  def get_headerEntries(self, sheetname):
    """
    Convenience method to return all header tuples.

    Keyword arguments:
    sheetname -- name of the sheet to extract from (self.pres_sheetname
    or self.edit_sheetname)
    """

    sheet = self.wb.sheet_by_name(sheetname)
    header_entries = []

    for i in range(0, sheet.ncols):
      header_entries.append(self.get_headerEntryAsTuple(sheetname, i))

    return header_entries


  def get_headerEntryAsTuple(self, sheetname, column):
    """
    Returns tuple of header archiving by stepping backwards from a
    3rd-level header.

    Keyword arguments:
    sheetname -- name of the sheet to extract from (self.pres_sheetname
    or self.edit_sheetname)
    column -- index of the column of the 3rd-level header
    """

    sheet = self.wb.sheet_by_name(sheetname)

    key1, key2, key3 = None, None, None

    key3 = sheet.cell(2, column).value

    j = column
    key2 = sheet.cell(1, j).value
    while not key2:
      j -= 1
      if j == -1:
        key2 = ""
        j = column
        break
      key2 = sheet.cell(1, j).value
    k = column
    key1 = sheet.cell(0, k).value
    while not key1:
      k -= 1
      key1 = sheet.cell(0, k).value

    entry = (str(key1), str(key2), str(key3))

    #Create filename tuple in problematic templates
    if (column == 0 and (not key3 or key1 == '\xa0')):
      entry = ("Reference filename (automatic)", None, None)

    return entry


  def get_headerEntryAsString(self, sheetname, column, delimiter = "|"):
    """
    Returns delimited string based on the output of
    get_headerEntryAsTuple()

    Keyword arguments:
    sheetname -- name of the sheet to extract from (self.pres_sheetname
    or self.edit_sheetname)
    column -- index of the column of the 3rd-level header
    delimiter -- character to separate tuple entries
    """

    header_entry = self.get_headerEntryAsTuple(sheetname, column)

    header_entry_list = [entry.lower() if entry else None for entry in header_entry]

    #remove empty tuple values before adding delimiter
    header_string = delimiter.join(filter(None, header_entry_list))

    #remove newlines since they're inconsistent
    header_string = header_string.replace("\n", " ").strip()

    return header_string


  def remove_annoying(self, val1, val2, expected, found):
    """
    Convenience function to remove items with XOR requirements

    Keyword arguments:
    val1 -- first XOR item
    val2 -- seocnd XOR item
    expected -- set of all required items
    found -- set of items that were extracted from sheet
    """

    if ((val1 in expected and val1 in found) and
      (val2 not in found)):
      expected.remove(val2)

    if ((val2 in expected and val2 in found) and
      (val1 not in found)):
      expected.remove(val1)

    return expected


  def check_headerRow(self, expected, found):
    """
    Check that a row of headers contains all the required values

    Keyword arguments:
    expected -- set of all required header values
    found -- set of items that were extracted from sheet
    """

    # spreadsheets must have either a barcode field or a object ID field, but both are not required
    header1 = 'Barcode'
    header2 = ('Object identifier\n(edit heading to specify type' +
      ' - e.g. barcode)')
    expected = self.remove_annoying(header1, header2, expected, found)

    missing = []

    for header in expected:
      if header not in found:
        missing.append(header)

    if missing:
      self.raise_excelerror("Missing required value- {0}."
        .format(missing))

    return True


  def check_headerEntries(self, expected, found):
    """
    Check that a sheet contains the required heirarchy of headers

    Keyword arguments:
    expected -- set of all required header heirarchies values
    found -- set of header heirarchies that were extracted from sheet
    """

    # spreadsheets must have either a barcode field or a object ID field, but both are not required
    header1 = ('Original master', 'Object', 'Barcode')
    header2 = ('Original master', 'Object',
      'Object identifier\n(edit heading to specify type ' +
      '- e.g. barcode)')
    expected = self.remove_annoying(header1, header2, expected, found)

    bad_entries = []

    for header in expected:
      if header not in found:
        bad_entries.append(header)

    if bad_entries:
      self.raise_excelerror("Incorrect header entry for {0}."
        .format(bad_entries))
    return True


  def check_noequations(self, sheetname):
    """
    Verify that no column in a sheet contains an equation
    Based on checking every cell in the 4th row

    Keyword arguments:
    sheetname -- name of the sheet to normalize (self.pres_sheetname or
    self.edit_sheetname)
    """

    self.wb_open = load_workbook(self.name, read_only = True)
    sheet = self.wb_open.get_sheet_by_name(sheetname)

    for i in range(1, self.wb.sheet_by_name(sheetname).ncols):
      value = sheet.cell(row = 4, column = i).value
      # equation check logic, might be better code out there
      if (value and isinstance(value, str) and value[0] == "="):
        self.raise_excelerror("Cell R4C{0} contain equations."
          .format(i))
    return True


  def normalize_excelSheet(self, sheetname, conversion_dictionary):
    """
    Convert Excel sheet into pandas dataframe
    Each list represents one row of the spreadsheets
    Header values are normalized based on dictionary
    Datetime values are automatically converted to ISO formats
    Row values are normalized based on dictionary

    Keyword arguments:
    sheetname -- name of the sheet to normalize (self.pres_sheetname or
    self.edit_sheetname)
    conversion_dictionary -- dict where keys are values from
    self.get_headerEntryAsString and values are normalized
    dot-formatted strings
    """

    sheet = self.wb.sheet_by_name(sheetname)

    ami_data = []

    date_headers = ["bibliographic.date", "technical.dateCreated"]
    time_headers = ["technical.durationHuman"]

    #copy everything from the 3rd row to the last row with a filename
    for rownum in range(2, sheet.nrows):
      if sheet.cell(rownum, 0):
        ami_data.append(sheet.row_values(rownum))

    for i in range(0, sheet.ncols):
      #normalize header
      header_entry = self.get_headerEntryAsString(sheetname, i)
      ami_data[0][i] = self.normalize_headerEntry(
        header_entry,
        conversion_dictionary)

      #convert excel dates
      if ami_data[0][i] in date_headers:
        for j in range(3, sheet.nrows):
          if sheet.cell(j, i).ctype == 3:
            value = sheet.cell(j, i).value
            ami_data[j-2][i] = self.convert_excelDateTime(value, "date")

      #convert excel times
      if ami_data[0][i] in time_headers:
        for j in range(3, sheet.nrows):
          if sheet.cell(j, i).ctype == 3:
            value = sheet.cell(j, i).value
            ami_data[j-2][i] = self.convert_excelDateTime(value, "time")

    ami_df = self.normalize_values(ami_data)

    return ami_df


  def normalize_headerEntry(self, header_entry, conversion_dictionary):
    """
    Returns a normalized dot-formatted string based on the
    heirarchy of headers from the first three rows of the Excel sheet.

    Keyword arguments:
    header_entry -- string of header values
    conversion_dictionary -- dict where keys are values from
    self.get_headerEntryAsString and values are normalized
    dot-formatted strings
    """

    if header_entry not in conversion_dictionary.keys():
      print(header_entry)
    return conversion_dictionary[header_entry]


  def convert_excelDateTime(self, value, return_type):
    """
    Converts Excel's decimal encoded datetimes into ISO format strings.
    Returns blank string if xldate conversion fails, otherwise, ISO
    string.

    Keyword arguments:
    value -- decimal number encoding Excel datetimes
    return_type -- (date, time) whether to return date or time
    """

    try:
      converted_value = xldate.xldate_as_datetime(value,
        self.wb.datemode)
      if return_type == "date":
        converted_value = converted_value.date().isoformat()
      if return_type == "time":
        converted_value = converted_value.time().isoformat()
    except:
      converted_value = ""

    return converted_value


  def normalize_values(self, data):
    """
    Normalize all entries via dictionaries defined in the ami_md_constants
    module. Returns a list of lists

    Keyword arguments:
    data -- a list of lists where each list represents a row and the
    first list contains headers
    """

    df = pd.DataFrame(data[1:], columns = data[0]).astype(str)

    df = df.replace(ami_md_constants.NAS)

    df = df.replace(ami_md_constants.REGEX_REPLACE_DICT, regex=True)
    df = df.replace(ami_md_constants.STRING_REPLACE_DICT)
    df['source.object.format_type'] = df['source.object.format'].map(ami_md_constants.FORMAT_TYPE)

    for key in ami_md_constants.MEASURE_UNIT_MAPS.keys():
      value_map = ami_md_constants.MEASURE_UNIT_MAPS[key]
      df = self.map_value(df,
        value_map['from_column'],
        value_map['to_column'],
        value_map['constant_value'],
        value_map['values_map_column'],
        value_map['values_map'])

    #force all the numerics back to numeric, and drop all empty columns
    df = df.apply(pd.to_numeric, errors='ignore').dropna(axis=1, how = "all")

    vals = df.values.tolist()
    cols = df.columns.tolist()
    vals.insert(0, cols)

    return vals


  def map_value(self, df, from_column, to_column, value = None,
    values_map_column = None, values_map = None):
    """
    Conditionally map units for columns with measures

    Keyword arguments:
    df -- pandas dataframe to operate on
    from_column -- name of column to map from
    to_column -- name of column to map new values to
    value -- constant value to map into to_column
    values_map_column -- name of column to determin variable mapping
    values_map -- dictionary of mapping values
    """
    if from_column not in df.columns:
      return df

    if value:
      df[to_column] = np.where(df[from_column].notnull(), value, None)
    elif values_map_column and values_map:
      #add unit value regardless if there is a measure value
      df[to_column] = df[values_map_column].map(values_map)
      #reset all unit values where there's no corresponding measure
      df[to_column] = df[to_column].mask(df[from_column].isnull(), None)

    return df



  def write_amiCSV(self, sheetname, conversion_dictionary, csv_filename):
    """
    Convert a single Excel sheet into a CSV with normalized contents.

    Keyword arguments:
    sheetname -- name of the sheet to convert (self.pres_sheetname or
    self.edit_sheetname)
    conversion_dictionary -- dict where keys are values from
    self.get_headerEntryAsString and values are normalized
    dot-formatted strings
    csv_filename -- path of the output file
    """

    ami_data = self.normalize_excelSheet(sheetname,
      conversion_dictionary)

    with open(csv_filename, 'w') as f:
      cw = csv.writer(f, quoting = csv.QUOTE_ALL)
      for rownum in range(0, len(ami_data)):
        cw.writerow(ami_data[rownum])


  def convert_amiExcelToJSON(self, sheetname, json_directory,
     conversion_dictionary = ami_md_constants.HEADER_CONVERSION):
    """
    Convert all rows in an Excel sheet into JSON files with
    normalized data. Filename is based on described file's name.

    Keyword arguments:
    sheetname -- name of the sheet to convert (self.pres_sheetname or
    self.edit_sheetname)
    conversion_dictionary -- dict where keys are values from
    self.get_headerEntryAsString and values are normalized
    dot-formatted strings
    json_directory -- path to output directory for json files
    """

    ami_data = self.normalize_excelSheet(sheetname,
      conversion_dictionary)

    cols = len(ami_data[0])

    headers = ami_data[0]

    json_directory = os.path.abspath(json_directory)

    for row in ami_data[1:]:
      tree = dict(zip(headers, row))
      json_tree = ami_json.ami_json(flat_dict = tree)
      json_tree.write_json(json_directory)


  def raise_excelerror(self, msg):
    """
    lazy error reporting
    """

    raise AMIExcelError(msg)
    logging.error(msg + '\n')
    return False
