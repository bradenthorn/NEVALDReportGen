# =================================================================================
# This script is used to pull the desired athletes data from VALD Hub using API
# Doesn't return anything just updates the Output CSVs (Full_Data.csv)
# Output CSVs are then used to creat the athletes PDF report
# Pulling athlete data from VALD Hub is a four step process:
# 1.) Authentication - Obtain VALD access token (using enviorment credentials)
# 2.) Fetch All Profiles - get profiles to map names to IDs
# 3.) Fetch Athlete Test Sessions - gives all athletes tests from a given date range
# 4.) Fetch Test Session Data - gives all data from a given test session
# 5.) Select Best Trials and Save CSVs - ends with a data frame of athletes best data
# NOTE: This script could be cleaner, but it definetely should work for now
#          Lots of prints right now that can eventually be removed
#          Also should probably check how we select the best results
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
from datetime import datetime
import pandas as pd
import sys
import pathlib
from typing import Optional
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
from ReportScripts.VALD_API.vald_client import ValdClient
from ReportScripts.VALD_API.VALDapiHelpers import cmj_z_score

# Temporarily need to manuall put test session in:
#TEMP_TEST_SESSION = datetime(2025, 7, 1).date() # July 1, 2025 (Charles Gargus)
#TEMP_TEST_SESSION = datetime(2025, 6, 29).date() # July 29, 2025 (Dylan Tostrup)
#TEMP_TEST_SESSION = datetime(2025, 8, 3).date() # August 1, 2025 (Braden Thorn)

# -- FUNCTIONS --------------------------------------------------------------------
def get_athlete_data(
    athlete_name: str,
    test_date: datetime,
    client: Optional[ValdClient] = None,
):
    """Pull and save athlete data for the specified test date."""
    athlete_name = athlete_name.lower().strip()
    if client is None:
        client = ValdClient()

    # Step 1 & 2: Get profiles and map athlete name to ID
    profiles = client.get_profiles()
    if profiles.empty:
        print("No profiles found. Try again. Exiting.")
        return None
    profiles["fullName"] = profiles["fullName"].str.lower().str.strip()
    athlete_row = profiles[profiles["fullName"] == athlete_name]
    if athlete_row.empty:
        print("Athlete not found. Check name spelling and spaces. Exiting.")
        return None
    profile_id = athlete_row.iloc[0]["profileId"]

    # Step 3: Fetch all test sessions for the athlete
    first_vald_date = datetime(2020, 1, 1, 0, 0, 0)
    test_sessions = client.get_tests_by_profile(first_vald_date, profile_id)
    if test_sessions is None:
        print("No test sessions found for athlete.")
        return None
    test_sessions = test_sessions[test_sessions["modifiedDateUtc"] == test_date]
    if test_sessions.empty:
        print("No test sessions found for the given date. Try again.")
        return None

    # Step 4: Fetch test session data (gives all 4 tests and all trials)
    test_IDandType_list = list(zip(test_sessions["testType"], test_sessions["testId"]))
    for testType, testID in test_IDandType_list:
        client.get_fd_results(testID, testType)

    # Step 5: Select best trials and merge data
    cmj_df = pd.read_csv("Output CSVs/Athlete/CMJ.csv")
    cmj_trial_columns = [col for col in cmj_df.columns if col.startswith("trial")]
    cmj_trial_z_scores = []
    for trial in cmj_trial_columns:
        trial_score = cmj_z_score(
            pd.to_numeric(cmj_df[cmj_df["metric_id"] == "CONCENTRIC_IMPULSE_Trial_Ns"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df["metric_id"] == "ECCENTRIC_BRAKING_RFD_Trial_N/s"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df["metric_id"] == "PEAK_CONCENTRIC_FORCE_Trial_N"][trial].values[0]),
            pd.to_numeric(
                cmj_df[cmj_df["metric_id"] == "BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg"][trial].values[0]
            ),
            pd.to_numeric(cmj_df[cmj_df["metric_id"] == "RSI_MODIFIED_Trial_RSI_mod"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df["metric_id"] == "ECCENTRIC_BRAKING_IMPULSE_Trial_Ns"][trial].values[0]),
        )
        cmj_trial_z_scores.append(round(float(trial_score), 5))

    best_trial = cmj_trial_z_scores.index(max(cmj_trial_z_scores)) + 1
    cmj_df = cmj_df[["metric_id", f"trial {best_trial}"]]
    cmj_df["metric_id"] = "CMJ_" + cmj_df["metric_id"]
    cmj_df.rename(columns={f"trial {best_trial}": "Value"}, inplace=True)

    # HJ: average best 5 RSI values (excluding highest)
    hj_df = pd.read_csv("Output CSVs/Athlete/HJ.csv")
    hj_trial_columns = [col for col in hj_df.columns if col.startswith("trial")]
    rsi_values = [round(float(hj_df[hj_df["metric_id"] == "HOP_RSI_Trial_"][trial].values[0]), 5) for trial in hj_trial_columns]
    rsi_values.sort(reverse=True)
    average_rsi = sum(rsi_values[1:6]) / 5
    new_row = {"metric_id": "HJ_AVJ_RSI_Trial_", "Value": average_rsi}
    cmj_df = pd.concat([cmj_df, pd.DataFrame([new_row])], ignore_index=True)

    # IMTP: take trial with highest peak vertical force
    imtp_df = pd.read_csv("Output CSVs/Athlete/IMTP.csv")
    imtp_trial_columns = [col for col in imtp_df.columns if col.startswith("trial")]
    peak_values = [
        round(float(imtp_df[imtp_df["metric_id"] == "PEAK_VERTICAL_FORCE_Trial_N"][trial].values[0]), 5)
        for trial in imtp_trial_columns
    ]
    best_trial = peak_values.index(max(peak_values)) + 1
    rel_value = round(
        float(
            imtp_df[imtp_df["metric_id"] == "ISO_BM_REL_FORCE_PEAK_Trial_N/kg"][f"trial {best_trial}"].values[0]
        ),
        5,
    )
    new_rows = [
        {"metric_id": "IMTP_PEAK_VERTICAL_FORCE_Trial_N", "Value": peak_values[best_trial - 1]},
        {"metric_id": "IMTP_ISO_BM_REL_FORCE_PEAK_Trial_N/kg", "Value": rel_value},
    ]
    cmj_df = pd.concat([cmj_df, pd.DataFrame(new_rows)], ignore_index=True)

    # PPU: take trial with best peak concentric force
    ppu_df = pd.read_csv("Output CSVs/Athlete/PPU.csv")
    ppu_trial_columns = [col for col in ppu_df.columns if col.startswith("trial")]
    peak_values = [
        round(float(ppu_df[ppu_df["metric_id"] == "PEAK_CONCENTRIC_FORCE_Trial_N"][trial].values[0]), 5)
        for trial in ppu_trial_columns
    ]
    best_trial = peak_values.index(max(peak_values)) + 1
    ppu_df = ppu_df[["metric_id", f"trial {best_trial}"]]
    ppu_df.rename(columns={f"trial {best_trial}": "Value"}, inplace=True)
    ppu_df["metric_id"] = "PPU_" + ppu_df["metric_id"]
    cmj_df = pd.concat([cmj_df, ppu_df], ignore_index=True)

    cmj_df.to_csv("Output CSVs/Athlete/Full_Data.csv", index=False)
    return cmj_df

