# =================================================================================
# This script is used to pull the HJ reference data from the GCP BigQuery database
# Not only will this script/function pull, but ideally it will clean the data as well
# Returns a pandas dataframe with the HJ reference data (doesn' save to a file)
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import HJ_TABLE
from ReportScripts.PullRefData.pull_ref_data import pull_ref


def pull_hj_ref(min_age: int, max_age: int) -> pd.DataFrame:
    df = pull_ref(HJ_TABLE, min_age, max_age)
    df = df.sort_values(by="hop_rsi_avg_best_5", ascending=False)
    df = df.drop_duplicates(subset=["athlete_name"], keep="first")
    return df