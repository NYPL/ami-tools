EXTS = [".mov", ".wav", ".mkv", ".iso", ".tar", ".mp4"]


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
