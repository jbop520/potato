import os
from pathlib import Path

class Config:

    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASS", "123456")
    DB_NAME = os.getenv("DB_NAME", "potato")

    COLD_LINKS = os.getenv("COLD_LINKS", "cold_links")

    TABLE_C804 = os.getenv("TABLE_C804", "ref_c804")
    TABLE_C882 = os.getenv("TABLE_C882", "ref_c882")
    LINKS_804_882 = os.getenv("LINKS_804_882","links_804_882")
    TABLE_C804_C882_PROTEIN_FILTER = os.getenv("TABLE_C804_C882_PROTEIN_FILTER", "c804_c882_protein_filter")
    TABLE_C882_C804_PROTEIN_FILTER = os.getenv("TABLE_C882_C804_PROTEIN_FILTER", "c882_c804_protein_filter")
    TRANSCRIPTOMICS_TOOL =os.getenv("TRANSCRIPTOMICS_TOOL", "transcriptomics_tool")

    BACTERIAL_WILT_REF_C454 =os.getenv("BACTERIAL_WILT_REF_C454","bacterial_wilt_ref_c454")
    BACTERIAL_WILT_REF_C804 = os.getenv("BACTERIAL_WILT_REF_C804", "bacterial_wilt_ref_c804")
    BACTERIAL_WILT_REF_C830 = os.getenv("BACTERIAL_WILT_REF_C830", "bacterial_wilt_ref_c830")
    BACTERIAL_WILT_REF_C882 = os.getenv("BACTERIAL_WILT_REF_C882", "bacterial_wilt_ref_c882")
    BACTERIAL_WILT_REF_DM = os.getenv("BACTERIAL_WILT_REF_DM", "bacterial_wilt_ref_dm")
    BACTERIAL_WILT_REF_T206 = os.getenv("BACTERIAL_WILT_REF_T206", "bacterial_wilt_ref_t206")

    COLD_AC_CANDOL_M4_2H_REF_C454 = os.getenv("COLD_AC_CANDOL_M4_2H_REF_C454","cold_ac_candol_m4_2h_ref_c454")
    COLD_AC_CANDOL_M4_2H_REF_C804 = os.getenv("COLD_AC_CANDOL_M4_2H_REF_C804", "cold_ac_candol_m4_2h_ref_c804")
    COLD_AC_CANDOL_M4_2H_REF_C830 = os.getenv("COLD_AC_CANDOL_M4_2H_REF_C830", "cold_ac_candol_m4_2h_ref_c830")
    COLD_AC_CANDOL_M4_2H_REF_C882 = os.getenv("COLD_AC_CANDOL_M4_2H_REF_C882", "cold_ac_candol_m4_2h_ref_c882")
    COLD_AC_CANDOL_M4_2H_REF_DM = os.getenv("COLD_AC_CANDOL_M4_2H_REF_DM", "cold_ac_candol_m4_2h_ref_dm")
    COLD_AC_CANDOL_M4_2H_REF_T206 = os.getenv("COLD_AC_CANDOL_M4_2H_REF_T206", "cold_ac_candol_m4_2h_ref_t206")

    COLD_AC_M3_REF_C830 = os.getenv("COLD_AC_M3_REF_C830","cold_ac_m3_ref_c830")
    COLD_AC_M3_REF_C454 = os.getenv("COLD_AC_M3_REF_C454", "cold_ac_m3_ref_c454")
    COLD_AC_M3_REF_C804 = os.getenv("COLD_AC_M3_REF_C804", "cold_ac_m3_ref_c804")
    COLD_AC_M3_REF_C882 = os.getenv("COLD_AC_M3_REF_C882", "cold_ac_m3_ref_c882")
    COLD_AC_M3_REF_DM = os.getenv("COLD_AC_M3_REF_DM", "cold_ac_m3_ref_dm")
    COLD_AC_M3_REF_T206 = os.getenv("COLD_AC_M3_REF_T206", "cold_ac_m3_ref_t206")

    COLD_AC_M4_2H_REF_C454 = os.getenv("COLD_AC_M4_2H_REF_C454","cold_ac_m4_2h_ref_c454")
    COLD_AC_M4_2H_REF_C804 = os.getenv("COLD_AC_M4_2H_REF_C804", "cold_ac_m4_2h_ref_c804")
    COLD_AC_M4_2H_REF_C830 = os.getenv("COLD_AC_M4_2H_REF_C830", "cold_ac_m4_2h_ref_c830")
    COLD_AC_M4_2H_REF_C882 = os.getenv("COLD_AC_M4_2H_REF_C882", "cold_ac_m4_2h_ref_c882")
    COLD_AC_M4_2H_REF_DM = os.getenv("COLD_AC_M4_2H_REF_DM", "cold_ac_m4_2h_ref_dm")
    COLD_AC_M4_2H_REF_T206 = os.getenv("COLD_AC_M4_2H_REF_T206", "cold_ac_m4_2h_ref_t206")

    COLD_NAC_M4_3H_REF_C454 = os.getenv("COLD_NAC_M4_3H_REF_C454","cold_nac_m4_3h_ref_c454")
    COLD_NAC_M4_3H_REF_C804 = os.getenv("COLD_NAC_M4_3H_REF_C804", "cold_nac_m4_3h_ref_c804")
    COLD_NAC_M4_3H_REF_C830 = os.getenv("COLD_NAC_M4_3H_REF_C830", "cold_nac_m4_3h_ref_c830")
    COLD_NAC_M4_3H_REF_C882 = os.getenv("COLD_NAC_M4_3H_REF_C882", "cold_nac_m4_3h_ref_c882")
    COLD_NAC_M4_3H_REF_DM = os.getenv("COLD_NAC_M4_3H_REF_DM", "cold_nac_m4_3h_ref_dm")
    COLD_NAC_M4_3H_REF_T206 = os.getenv("COLD_NAC_M4_3H_REF_T206", "cold_nac_m4_3h_ref_t206")

    TUBER_DEVELOPMENT_REF_C454 = os.getenv("TUBER_DEVELOPMENT_REF_C454", "tuber_development_ref_c454")
    TUBER_DEVELOPMENT_REF_C804 = os.getenv("TUBER_DEVELOPMENT_REF_C804", "tuber_development_ref_c804")
    TUBER_DEVELOPMENT_REF_C830 = os.getenv("TUBER_DEVELOPMENT_REF_C830", "tuber_development_ref_c830")
    TUBER_DEVELOPMENT_REF_C882 = os.getenv("TUBER_DEVELOPMENT_REF_C882", "tuber_development_ref_c882")
    TUBER_DEVELOPMENT_REF_DM = os.getenv("TUBER_DEVELOPMENT_REF_DM", "tuber_development_ref_dm")
    TUBER_DEVELOPMENT_REF_T206 = os.getenv("TUBER_DEVELOPMENT_REF_T206", "tuber_development_ref_t206")

    MULTIPLE_TREATMENTS_REF_C830 = os.getenv("MULTIPLE_TREATMENTS_REF_C830", "multiple_treatments_ref_c830")
    MULTIPLE_TREATMENTS_REF_C454 = os.getenv("MULTIPLE_TREATMENTS_REF_C454", "multiple_treatments_ref_c454")
    MULTIPLE_TREATMENTS_REF_C804 = os.getenv("MULTIPLE_TREATMENTS_REF_C804", "multiple_treatments_ref_c804")
    MULTIPLE_TREATMENTS_REF_C882 = os.getenv("MULTIPLE_TREATMENTS_REF_C882", "multiple_treatments_ref_c882")
    MULTIPLE_TREATMENTS_REF_DM = os.getenv("MULTIPLE_TREATMENTS_REF_DM", "multiple_treatments_ref_dm")
    MULTIPLE_TREATMENTS_REF_T206 = os.getenv("MULTIPLE_TREATMENTS_REF_T206", "multiple_treatments_ref_t206")

    SALT_48H_REF_C454 = os.getenv("SALT_48H_REF_C454","salt_48h_ref_c454")
    SALT_48H_REF_C804 = os.getenv("SALT_48H_REF_C804", "salt_48h_ref_c804")
    SALT_48H_REF_C830 = os.getenv("SALT_48H_REF_C830", "salt_48h_ref_c830")
    SALT_48H_REF_C882 = os.getenv("SALT_48H_REF_C882", "salt_48h_ref_c882")
    SALT_48H_REF_DM = os.getenv("SALT_48H_REF_DM", "salt_48h_ref_dm")
    SALT_48H_REF_T206 = os.getenv("SALT_48H_REF_T206", "salt_48h_ref_t206")

    BASE_FILES_DIR = Path(os.getenv("BASE_FILES_DIR", r"D:\potato\二、基因组")).resolve()
