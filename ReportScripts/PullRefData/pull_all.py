# =================================================================================
# This script is used to pull all the reference data from the GCP BigQuery database
# This will rely on the independent pull scripts for each test type
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import pathlib
import sys
from typing import Dict

import pandas as pd

# Add project root to path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import (
    CMJ_TABLE,
    HJ_TABLE,
    IMTP_TABLE,
    PPU_TABLE,
)
from ReportScripts.PullRefData.pull_ref_data import pull_ref


def pull_all_ref(min_age: int, max_age: int) -> Dict[str, 'pd.DataFrame']:
    """Fetch reference data for all tests and return them in a dictionary."""
    test_configs = [
        (CMJ_TABLE, "cmj", "cmj_composite_score"),
        (HJ_TABLE, "hj", "hop_rsi_avg_best_5"),
        (IMTP_TABLE, "imtp", "ISO_BM_REL_FORCE_PEAK_Trial_N_kg"),
        (PPU_TABLE, "ppu", "PEAK_CONCENTRIC_FORCE_Trial_N"),
    ]

    ref_data: Dict[str, 'pd.DataFrame'] = {}
    for table, key, sort_col in test_configs:
        df = pull_ref(table, min_age, max_age)
        df = df.sort_values(by=sort_col, ascending=False)
        df = df.drop_duplicates(subset=["athlete_name"], keep="first")
        ref_data[key] = df

    return ref_data
