import re

FILENAME_REGEX = re.compile(
    "[a-z]{3}_[a-z0-9]+_v\d{2}(([frspt]\d{2})+)?_(pm|em|sc|pf|assetfront|assetback)\.[a-z0-9]+",
    re.IGNORECASE)
SUBOBJECT_REGEX = re.compile("_v\d{2}(f\d{2})?([rspt]\d{2})+")

MD_DIR = "Metadata"
PM_DIR = "PreservationMasters"
EM_DIR = "EditMasters"
SC_DIR = "ServiceCopies"
AO_DIR = "ArchiveOriginals"
PF_DIR = "ProjectFiles"
IM_DIR = "Images"

MOV_EXT = ".mov"
MKV_EXT = ".mkv"
MP4_EXT = ".mp4"
ISO_EXT = ".iso"
TAR_EXT = ".tar"
WAV_EXT = ".wav"
EXCEL_EXT = ".xlsx"
EDITEDEXCEL_EXT = ".old"
JSON_EXT = ".json"
JPEG_EXT = ".jpeg"

MEDIA_EXTS = [MOV_EXT, MKV_EXT, MP4_EXT, ISO_EXT, TAR_EXT, WAV_EXT]

EXCEL_SUBTYPES = {
    "video": ([MD_DIR, PM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, MOV_EXT]),
    "dvd": ([MD_DIR, PM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, ISO_EXT]),
    "audio": ([MD_DIR, PM_DIR, EM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, WAV_EXT]),
    "audio w/o edit masters": ([MD_DIR, PM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, WAV_EXT]),
    "born-digital video": ([MD_DIR, AO_DIR, EM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, TAR_EXT, MOV_EXT]),
    "born-digital audio": ([MD_DIR, AO_DIR, EM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, WAV_EXT])
}

EXCEL_SUBTYPES = {
    "video": ([PM_DIR, SC_DIR, IM_DIR],
        [JSON_EXT, MOV_EXT, MKV_EXT, MP4_EXT, JPEG_EXT]),
    "audio": ([PM_DIR, SC_DIR, IM_DIR],
        [JSON_EXT, WAV_EXT, JPEG_EXT])
}

EXCELJSON_SUBTYPES = {
    "audio": ([MD_DIR, PM_DIR, SC_DIR, IM_DIR],
        [EXCEL_EXT, EDITEDEXCEL_EXT, JSON_EXT, WAV_EXT, JPEG_EXT])
}
