# =================================================================================
# This script is used to pull all the reference data from the GCP BigQuery database
# This will rely on the independent pull scripts for each test type
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import pathlib
import sys
from pathlib import Path

# Add project root to path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import (
    OUTPUT_DIR,
    CMJ_TABLE,
    HJ_TABLE,
    IMTP_TABLE,
    PPU_TABLE,
)
from ReportScripts.PullRefData.pull_ref_data import pull_ref


def pull_all_ref(min_age: int, max_age: int):
    ref_dir = Path(OUTPUT_DIR) / "Reference"
    ref_dir.mkdir(parents=True, exist_ok=True)

    test_configs = [
        (CMJ_TABLE, "CMJ_ref.csv", "cmj_composite_score"),
        (HJ_TABLE, "HJ_ref.csv", "hop_rsi_avg_best_5"),
        (IMTP_TABLE, "IMTP_ref.csv", "ISO_BM_REL_FORCE_PEAK_Trial_N_kg"),
        (PPU_TABLE, "PPU_ref.csv", "PEAK_CONCENTRIC_FORCE_Trial_N"),
    ]

    for table, filename, sort_col in test_configs:
        df = pull_ref(table, min_age, max_age)
        df = df.sort_values(by=sort_col, ascending=False)
        df = df.drop_duplicates(subset=["athlete_name"], keep="first")
        df.to_csv(ref_dir / filename, index=False)

