import os
from pymediainfo import MediaInfo
from datetime import datetime

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
        self.format = track.format
        self.size = track.file_size

        if track.encoded_date:
          self.date_created = track.encoded_date.split()[0].replace(":", "-")
        elif track.recorded_date:
          self.date_created = track.recorded_date.split()[0].replace(":", "-")

        for duration in track.other_duration:
          try:
            datetime.strptime(duration, '%H:%M:%S.%f')
          except:
            continue
          else:
            self.duration_human = duration
            break

        self.duration_milli = track.duration

      elif track.track_type == "Audio":
        self.audio_codec = track.codec
      elif track.track_type == "Video":
        self.video_codec = track.codec


  def raise_jsonerror(self, msg):
    """
    lazy error reporting
    """
    logging.error(msg + '\n')
    raise AMIFileError(msg)
