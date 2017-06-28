import os
from pymediainfo import MediaInfo

class AMIFileError(Exception):
  def __init__(self, message):
    self.message = message
  def __str__(self):
    return repr(self.message)


class ami_file:
  def __init__(self, filepath):
    if os.path.isfile(filepath):
      self.filepath = os.path.abspath(filepath)
      self.filename = os.path.basename(self.filepath)
    else:
      self.raise_AMIFileError("Not an valid filepath")

    self.set_techmd_values()
    if hasattr(self, "video_codec"):
      self.type = "video"
    else:
      self.type = "audio"


  def set_techmd_values(self):
    techmd = MediaInfo.parse(self.filepath)

    for track in techmd.tracks:
      if track.track_type == "General":
        self.base_filename = track.file_name
        self.extension = track.file_extension
        self.file_format = track.format
        self.file_size = track.file_size
        if track.encoded_date:
          self.date_create = track.encoded_date.split()[0].replace(":", "-")
        elif track.recorded_date:
          self.date_create = track.recorded_date.split()[0].replace(":", "-")
        elif track.file_last_modification_date__local:
          self.date_create = track.file_last_modification_date__local.split()[0].replace(":", "-")
        self.duration_human = track.other_duration[-3]
        self.duration_milli = track.duration
      elif track.type == "Video":
        self.audio_codec = track.codec_id
      elif track.type == "Audio":
        self.video_codec = track.codec_id


  def raise_jsonerror(self, msg):
    """
    lazy error reporting
    """
    logging.error(msg + '\n')
    raise AMIFileError(msg)
