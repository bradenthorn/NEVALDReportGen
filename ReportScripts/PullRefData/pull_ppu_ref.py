# =================================================================================
# This script is used to pull the PPU reference data from the GCP BigQuery database
# Not only will this script/function pull, but ideally it will clean the data as well
# Returns a pandas dataframe with the PPU reference data (doesn' save to a file)
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from pathlib import Path

# -- CONSTANTS --------------------------------------------------------------------
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import GCP_CREDENTIALS_PATH, GCP_PROJECT_ID, PPU_TABLE

key_path = GCP_CREDENTIALS_PATH
project_id = GCP_PROJECT_ID
_TABLE_FQN = PPU_TABLE

# -- FUNCTIONS --------------------------------------------------------------------
def pull_ppu_ref(min_age: int, max_age: int) -> pd.DataFrame:
    # -- Step 1: Connect to the GCP BigQuery database -----------------------------
    creds  = service_account.Credentials.from_service_account_file(key_path)
    client = bigquery.Client(credentials=creds, project=project_id)
    
    # -- Step 2: Construct and execute the SQL query ------------------------------
    sql = f""" SELECT * 
               FROM `{_TABLE_FQN}` 
               WHERE age_at_test BETWEEN @min_age AND @max_age"""
    temp_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_age", "INT64", min_age),
            bigquery.ScalarQueryParameter("max_age", "INT64", max_age)
        ]
    )
    df = client.query(sql, job_config=temp_config).result().to_dataframe()

    # -- Step 3: Clean the data ---------------------------------------------------
    # Keeping only the best "PEAK_CONCENTRIC_FORCE_Trial_N" value for each athlete
    df = df.sort_values(by="PEAK_CONCENTRIC_FORCE_Trial_N", ascending=False)
    df = df.drop_duplicates(subset=["athlete_name"], keep="first")

    # -- Step 4: Returning the cleaned data ---------------------------------------
    return df