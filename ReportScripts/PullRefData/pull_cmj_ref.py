# =================================================================================
# This script is used to pull the CMJ reference data from the GCP BigQuery database
# Not only will this script/function pull, but ideally it will clean the data as well
# Returns a pandas dataframe with the CMJ reference data (doesn' save to a file)
# TODO: I think that instead of returning a df, we should save to a csv (Reference)
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
from pathlib import Path
import sys
import pandas as pd

# Add project root to path for config import
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import CMJ_TABLE
from ReportScripts.PullRefData.pull_ref_data import pull_ref


def pull_cmj_ref(min_age: int, max_age: int) -> pd.DataFrame:
    df = pull_ref(CMJ_TABLE, min_age, max_age)
    df = df.sort_values(by="cmj_composite_score", ascending=False)
    df = df.drop_duplicates(subset=["athlete_name"], keep="first")
    return df