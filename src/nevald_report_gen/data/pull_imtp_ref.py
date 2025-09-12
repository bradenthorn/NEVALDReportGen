# =================================================================================
# This script is used to pull the IMTP reference data from the GCP BigQuery database
# Not only will this script/function pull, but ideally it will clean the data as well
# Returns a pandas dataframe with the IMTP reference data (doesn' save to a file)
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
from pathlib import Path
import sys
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))
from nevald_report_gen.config import IMTP_TABLE
from nevald_report_gen.data.pull_ref_data import pull_ref


def pull_imtp_ref(min_age: int, max_age: int) -> pd.DataFrame:
    df = pull_ref(IMTP_TABLE, min_age, max_age)
    df = df.sort_values(by="PEAK_VERTICAL_FORCE_Trial_N", ascending=False)
    df = df.drop_duplicates(subset=["athlete_name"], keep="first")
    return df
    

