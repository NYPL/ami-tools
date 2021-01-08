MOV_EXT = ".mov"
DV_EXT = ".dv"
MKV_EXT = ".mkv"
MKA_EXT = ".mka"
MP4_EXT = ".mp4"
ISO_EXT = ".iso"
TAR_EXT = ".tar"
WAV_EXT = ".wav"
FLAC_EXT = ".flac"

MEDIA_EXTS = [MOV_EXT, DV_EXT, MKV_EXT, MKA_EXT, MP4_EXT, ISO_EXT, TAR_EXT, WAV_EXT, FLAC_EXT]

VIDEO_EXTS = [MOV_EXT, DV_EXT, MKV_EXT, MP4_EXT, ISO_EXT, TAR_EXT]
AUDIO_EXTS = [MKA_EXT, WAV_EXT, FLAC_EXT]

AO_ENDING = "ao"
PM_ENDING = "pm"
MZ_ENDING = "mz"
EM_ENDING = "em"
SC_ENDING = "sc"

FILE_ROLES = [AO_ENDING, PM_ENDING, EM_ENDING, SC_ENDING, MZ_ENDING]

FN_NOEXT_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(ao|pm|em|sc)$"
STUB_FN_NOEXT_RE = r"^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_(ao|pm|em|sc)"
FN_RE = "^[a-z]{3}_[a-z\d\-\*_]+_([vfrspt]\d{2})+_({roles}})\.({exts})$".format(roles = "|".join(FILE_ROLES), exts = "|".join(MEDIA_EXTS))