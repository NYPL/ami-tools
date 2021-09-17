import os
import logging
from pymediainfo import MediaInfo
from datetime import datetime
from dateutil import parser

import ami_files.ami_file_constants as ami_file_constants

LOGGER = logging.getLogger(__name__)

class AMIFileError(Exception):
  def __init__(self, message):
    self.message = message
  def __str__(self):
    return repr(self.message)


class ami_file:
  def __init__(self, filepath, mi = True):
    if os.path.isfile(filepath):
      self.filepath = os.path.abspath(filepath)
      self.filename = os.path.basename(self.filepath)
    else:
      self.raise_AMIFileError('{} is not a valid filepath'.format(filepath))
    
    if mi:
      self.set_techmd_values()
    else:
      self.date_filesys_created = datetime.fromtimestamp(os.path.getctime(self.filepath)).strftime('%Y-%m-%d')
      self.extension =  os.path.splitext(self.filepath)[1][1:]

    if self.extension.lower() in ami_file_constants.VIDEO_EXTS:
      self.type = "video"
    elif self.extension.lower() in ami_file_constants.AUDIO_EXTS:
      self.type = "audio"
    else:
      self.raise_AMIFileError('{} does not appear to be an accepted audio or video format.'.format(self.filename))


  def set_techmd_values(self):
    techmd = MediaInfo.parse(self.filepath)

    md_track = None
    for track in techmd.tracks:
      if track.track_type == "General":
        md_track = track

    if not md_track:
      self.raise_AMIFileError('Could not find General track')

    self.base_filename = md_track.file_name.rsplit('.')[0]
    self.extension = md_track.file_extension
    self.format = md_track.format
    self.size = md_track.file_size

    self.date_filesys_created = datetime.fromtimestamp(os.path.getctime(self.filepath)).strftime('%Y-%m-%d')
    if md_track.encoded_date:
      self.date_created = parse_date(md_track.encoded_date)
    elif md_track.recorded_date:
      self.date_created = parse_date(md_track.recorded_date)
    elif md_track.file_last_modification_date:
      self.date_created = self.date_filesys_created

    self.duration_milli = md_track.duration
    self.duration_human = parse_duration(self.duration_milli)

    if md_track.audio_codecs.contains('/'):
      self.audio_codec = '|'.join(set(x.strip() for x in md_track.audio_codecs.split('/')))
    else:
      self.audio_codec = md_track.audio_codecs.split("/")
    if md_track.codecs_video:
      self.video_codec = md_track.codecs_video


  def raise_AMIFileError(self, msg):
    """
    lazy error reporting
    """
    logging.error(msg + '\n')
    raise AMIFileError(msg)


def parse_date(date_string):
  try:
    parsed = parser.parse(date_string)
  except:
    try:
      parsed = datetime.strptime(date_string, '%Z %Y-%m-%d %H:%M:%S')
    except:
      raise ValueError

  return parsed.date().strftime('%Y-%m-%d')


def parse_duration(ms_int):
  if not ms_int:
    return None

  hours = ms_int // 3600000
  minutes = (ms_int % 3600000) // 60000
  seconds = (ms_int % 60000) // 1000
  ms = ms_int % 1000
  return "{:0>2}:{:0>2}:{:0>2}.{:0>3}".format(hours, minutes, seconds, ms)
