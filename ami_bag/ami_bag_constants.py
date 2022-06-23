import re

FILENAME_REGEX = re.compile(
    "([a-z]{3}_[a-z0-9]+_v\d{2}(([frspt]\d{2})+)?_(ao|pm|mz|em|sc|pf|assetfront|assetback|assetside|boxfront|boxback|boxside|reelfront|ephemera)([~\d\-]+)?\.[a-z0-9]+)|(\d{4}_\d{3}_[\da-zA-Z_]+\.(xlsx|old))",
    re.IGNORECASE)
SUBOBJECT_REGEX = re.compile("_v\d{2}(f\d{2})?([rspt]\d{2})+")
SUBOBJECT_PART_REGEX = re.compile("_v\d{2}([frst\d]+)?(p|pt)\d{2}")

MD_DIR = "Metadata"
PM_DIR = "PreservationMasters"
MZ_DIR = "Mezzanines"
EM_DIR = "EditMasters"
SC_DIR = "ServiceCopies"
AO_DIR = "ArchiveOriginals"
PF_DIR = "ProjectFiles"
IM_DIR = "Images"

MOV_EXT = ".mov"
DV_EXT = ".dv"
MKV_EXT = ".mkv"
MKA_EXT = ".mka"
MP4_EXT = ".mp4"
ISO_EXT = ".iso"
TAR_EXT = ".tar"
WAV_EXT = ".wav"
FLAC_EXT = ".flac"
EXCEL_EXT = ".xlsx"
EDITEDEXCEL_EXT = ".old"
JSON_EXT = ".json"
JPEG_EXT = ".jpeg"
JPG_EXT = ".jpg"
PDF_EXT = ".pdf"
GZ_EXT = ".gz"
SRT_EXT = ".srt"
CUE_EXT = ".cue"
SCC_EXT = ".scc"

MEDIA_EXTS = [MOV_EXT, DV_EXT, MKV_EXT, MKA_EXT, MP4_EXT, ISO_EXT, TAR_EXT, WAV_EXT, FLAC_EXT]

EXCEL_SUBTYPES = {
    "video": (set([MD_DIR, PM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, MOV_EXT])),
    "dvd": (set([MD_DIR, PM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, ISO_EXT])),
    "audio": (set([MD_DIR, PM_DIR, EM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, WAV_EXT])),
    "audio w/o edit masters": (set([MD_DIR, PM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, WAV_EXT])),
    "born-digital video": (set([MD_DIR, PM_DIR, AO_DIR, EM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, TAR_EXT, MOV_EXT])),
    "born-digital audio": (set([MD_DIR, AO_DIR, EM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, WAV_EXT]))
}

JSON_SUBTYPES = {
    # order matters for ami_bag.set_subtype
    # subtype is permissive, so every video bag meets film bag spec
    # always check video after film
    "film": (set([PM_DIR, MZ_DIR, SC_DIR, IM_DIR]),
        set([JSON_EXT, MKV_EXT, MOV_EXT, MP4_EXT, JPEG_EXT, JPG_EXT, GZ_EXT, SRT_EXT, SCC_EXT])),
    "video": (set([PM_DIR, SC_DIR, IM_DIR]),
        set([JSON_EXT, MOV_EXT, MKV_EXT, DV_EXT, MP4_EXT, JPEG_EXT, JPG_EXT, GZ_EXT, SRT_EXT, SCC_EXT])),
    "audio": (set([PM_DIR, EM_DIR, IM_DIR]),
        set([JSON_EXT, WAV_EXT, FLAC_EXT, JPEG_EXT, JPG_EXT, CUE_EXT]))
}

EXCELJSON_SUBTYPES = {
    "audio": (set([MD_DIR, PM_DIR, SC_DIR, IM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, JSON_EXT, WAV_EXT, FLAC_EXT, JPEG_EXT, CUE_EXT])),
    "video": (set([MD_DIR, PM_DIR, SC_DIR, IM_DIR]),
        set([EXCEL_EXT, EDITEDEXCEL_EXT, JSON_EXT, MKV_EXT, MOV_EXT, DV_EXT, MP4_EXT, JPEG_EXT, GZ_EXT, SRT_EXT, SCC_EXT]))
}
