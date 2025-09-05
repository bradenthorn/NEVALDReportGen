# =================================================================================
# This script contains helper functions for the VALD API including:
# get_profiles - get all profiles from VALD Hub
# FD_Tests_by_Profile - get all FD tests by profile
# Clean FD Tests - clean the FD tests to only include dates with all 4 tests
# cmj_z_score - get the CMJ Z-Score for a given trial
# get_FD_results - get all FD results by test session
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import pathlib
import sys
from pathlib import Path
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
from config import OUTPUT_DIR
from ReportScripts.VALD_API.metric_vars import (METRICS_OF_INTEREST, unit_map)
from ReportScripts.VALD_API.token_gen import get_vald_token

# -- ENVIORMENT VARIABLES ---------------------------------------------------------
load_dotenv()
FORCEDECKS_URL = os.getenv("FORCEDECKS_URL")
DYNAMO_URL     = os.getenv("DYNAMO_URL")
PROFILE_URL    = os.getenv("PROFILE_URL")
TENANT_ID      = os.getenv("TENANT_ID")

# -- HELPER FUNCTIONS --------------------------------------------------------------
# Get all profiles from VALD Hub
def get_profiles(token):
    today = datetime.today()
    url = f"{PROFILE_URL}/profiles?tenantId={TENANT_ID}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    # Check if the response is successful
    if response.status_code == 200:
        # Convert response to pandas data frame
        df = pd.DataFrame(response.json()['profiles'])
        # Clean the data frame
        df['givenName']   = df['givenName'].str.strip().str.lower()
        df['familyName']  = df['familyName'].str.strip().str.lower()
        df['fullName']    = (df['givenName'] + ' ' + df['familyName']).str.title()
        # Keep only fullName and profileId
        df = df[['fullName', 'profileId']]
        # Return the data frame
        return df
    else:
        print(f"Failed to get profiles: {response.status_code}")
        return pd.DataFrame()
    
# Get all test sessions for a given profile (only returns dates with all 4 tests)
def FD_Tests_by_Profile(DATE, profileId, token):
    url=f"{FORCEDECKS_URL}/tests?TenantId={TENANT_ID}&ModifiedFromUtc={DATE}&ProfileId={profileId}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    # Check if the response is successful
    if response.status_code == 200:
        # Convert response to pandas data frame
        df = pd.DataFrame(response.json()['tests'])
        df = df[['testId', 'modifiedDateUtc', 'testType']]
        # Clean the data frame to only include dates with all 4 tests
        df['modifiedDateUtc'] = pd.to_datetime(df['modifiedDateUtc']).dt.date
        required_tests = set(['HJ', 'CMJ', 'PPU', 'IMTP'])
        test_types_per_date = df.groupby('modifiedDateUtc')['testType'].agg(set)
        valid_dates = test_types_per_date[test_types_per_date.apply(lambda x: required_tests.issubset(x))].index
        filtered_df = df[df['modifiedDateUtc'].isin(valid_dates)]
        # Checking if the data frame is empty (if so, athlete has no valid test sessions)
        if filtered_df.empty:
            print("No valid test sessions. Athlete must have HJ, CMJ, PPU, and IMTP tests. Test Dates:")
            print(df)
            return None
        else:
            return filtered_df
    else:
        print(f"Failed to get test sessions: {response.status_code}")

# Clean FD Tests - clean the FD tests to only include dates with all 4 tests


# Get CMJ Trial Z-Score to determine best trial (this works for now, but might be worse in the future)
def cmj_z_score(
    CONCENTRIC_IMPULSE_Trial_Ns,
    ECCENTRIC_BRAKING_RFD_Trial_Ns,
    PEAK_CONCENTRIC_FORCE_Trial_N,
    BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_Wkg,
    RSI_MODIFIED_Trial_RSI_mod,
    ECCENTRIC_BRAKING_IMPULSE_Trial_Ns,
):
    """Calculate a CMJ trial z-score used to select the best jump."""
    return (
        ((CONCENTRIC_IMPULSE_Trial_Ns * 0.0159412) - 2.739286) * 0.2
        + ((ECCENTRIC_BRAKING_RFD_Trial_Ns * 0.0004317) - 1.680167) * 0.1
        + ((PEAK_CONCENTRIC_FORCE_Trial_N * 0.0018574) - 2.995598) * 0.2
        + ((BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_Wkg) * 0.1045924) * 0.3
        + ((RSI_MODIFIED_Trial_RSI_mod) * 7.5804694) * 0.1
        + ((ECCENTRIC_BRAKING_IMPULSE_Trial_Ns) * 0.049517) * 0.1
    )

# Get FD results from a specific testID
def get_FD_results(testId, token, test_type):
    url = f"{FORCEDECKS_URL}/v2019q3/teams/{TENANT_ID}/tests/{testId}/trials"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    # Check if the response is successful
    if response.status_code == 200:
        test_data_json = response.json()
        # Check that the FD response is not empty and is in list format
        if not test_data_json or not isinstance(test_data_json, list):
            print("Unexpected response format.")
            return None
        # Converting the data to a pandas data frame
        all_results = []
        for trial in test_data_json:
            results = trial.get("results", [])
            for res in results:
                flat_result = {
                    "value": res.get("value"),
                    "limb": res.get("limb"),
                    "result_key": res["definition"].get("result", ""),
                    "unit": res["definition"].get("unit", "")
                }
                all_results.append(flat_result)
        # Check that the all_results list is not empty
        if not all_results:
            return None
        # Convert the list of dictionaries to a pandas data frame
        df = pd.DataFrame(all_results)
        df['unit'] = df['unit'].apply(unit_map)
        # Renaming columns, adding trial number, and pivoting
        df['metric_id'] = (df['result_key'].astype(str) + '_' + 
                           df['limb'].astype(str) + '_' +
                           df['unit'].astype(str))
        df['trial'] = df.groupby('metric_id').cumcount() + 1
        pivot = df.pivot_table(index='metric_id', columns='trial', values='value', aggfunc='first')
        pivot.columns = [f'trial {c}' for c in pivot.columns]
        pivot = pivot.reset_index()
        # Keeping only the metrics of interest
        pivot = pivot[pivot['metric_id'].isin(METRICS_OF_INTEREST[test_type])]
        # Returning the filtered data frame
        athlete_dir = Path(OUTPUT_DIR) / "Athlete"
        athlete_dir.mkdir(parents=True, exist_ok=True)
        pivot.to_csv(athlete_dir / f"{test_type}.csv")
        return pivot
    else:
        print(f"Failed to get FD results: {response.status_code}")



# Test code removed - uncomment below to test token generation
# test_token = get_vald_token()
# test = get_profiles(test_token)
# print(test.columns)
