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
from datetime import datetime, date
import pandas as pd
import sys
from pathlib import Path
import pathlib
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
from ReportScripts.VALD_API.VALDapiHelpers import (get_profiles, FD_Tests_by_Profile, 
                                                   get_FD_results, cmj_z_score)
from ReportScripts.VALD_API.token_gen import get_vald_token

# Temporarily need to manuall put test session in:
#TEMP_TEST_SESSION = datetime(2025, 7, 1).date() # July 1, 2025 (Charles Gargus)
#TEMP_TEST_SESSION = datetime(2025, 6, 29).date() # July 29, 2025 (Dylan Tostrup)
#TEMP_TEST_SESSION = datetime(2025, 8, 3).date() # August 1, 2025 (Braden Thorn)

# -- FUNCTIONS --------------------------------------------------------------------
def get_athlete_data(athlete_name: str, test_date: datetime):
    # Dealing with athlete name case sensitivity
    athlete_name = athlete_name.lower().strip()
    # Step 1: Get token
    token = get_vald_token()
    # Step 2: Get profiles from API and map athlete name to ID
    profiles = get_profiles(token)
    if profiles.empty:
        print("No profiles found. Try again. Exiting.")
        exit()
    profiles['fullName'] = profiles['fullName'].str.lower().str.strip()
    athlete_row = profiles[profiles['fullName'] == athlete_name]
    if not athlete_row.empty:
        profile_id = athlete_row.iloc[0]['profileId']
    else:
        print("Athlete not found. Check name spelling and spaces. Exiting.")
        exit()
    # Step 3: Fetch all test sessions for the athlete
    FIRST_VALD_DATE = datetime(2020, 1, 1, 0, 0, 0) # January 1st, 2020 (way before first test)
    test_sessions = FD_Tests_by_Profile(FIRST_VALD_DATE, profile_id, token)
    # TODO:At this point, we need a system (UI) to select the test session we want
    # For now, we will manually put test session in script (above this function definition)
    test_sessions = test_sessions[test_sessions['modifiedDateUtc'] == test_date]
    if test_sessions.empty:
        print("No test sessions found for the given date. Try again. Exiting.")
        exit()
    test_IDandType_list = list(zip(test_sessions['testType'], test_sessions['testId']))
    # Step 4: Fetch test session data (gives all 4 tests and all trials)
    for testType, testID in test_IDandType_list:
        get_FD_results(testID, token, testType)
    # Step 5: Select best trials and merge data (one df like victus had)
    cmj_df = pd.read_csv("Output CSVs/Athlete/CMJ.csv")
    # 5.1) CMJ: get only the trial columns (exclude the first column which is metric_id)
    cmj_trial_columns = [col for col in cmj_df.columns if col.startswith('trial')]
    # 5.1) CMJ: get the z-scores for each cmj trial
    cmj_trial_z_scores = []
    for trial in cmj_trial_columns:
        trial_score = cmj_z_score(
            pd.to_numeric(cmj_df[cmj_df['metric_id'] == "CONCENTRIC_IMPULSE_Trial_Ns"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df['metric_id'] == "ECCENTRIC_BRAKING_RFD_Trial_N/s"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df['metric_id'] == "PEAK_CONCENTRIC_FORCE_Trial_N"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df['metric_id'] == "BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df['metric_id'] == "RSI_MODIFIED_Trial_RSI_mod"][trial].values[0]),
            pd.to_numeric(cmj_df[cmj_df['metric_id'] == "ECCENTRIC_BRAKING_IMPULSE_Trial_Ns"][trial].values[0])
        )
        cmj_trial_z_scores.append(round(float(trial_score), 5))
    # 5.1) CMJ: select best trial score and keep only that cmj trial (resave to CMJ csv)
    # NOTE: Body weight is in Kg, so may need to figure that out
    best_trial = cmj_trial_z_scores.index(max(cmj_trial_z_scores)) + 1
    cmj_df = cmj_df[['metric_id', f'trial {best_trial}']]
    cmj_df['metric_id'] = 'CMJ_' + cmj_df['metric_id']
    cmj_df.rename(columns={f'trial {best_trial}': 'Value'}, inplace=True)
    # 5.2) HJ: AVJ the 5 best RSI's and upload to df (not including the highest RSI for misread issues)
    hj_df = pd.read_csv("Output CSVs/Athlete/HJ.csv")
    hj_trial_columns = [col for col in hj_df.columns if col.startswith('trial')]
    rsi_values = []
    for trial in hj_trial_columns:
        rsi_values.append(round(float(hj_df[hj_df['metric_id'] == "HOP_RSI_Trial_"][trial].values[0]), 5))
    rsi_values.sort(reverse=True)
    average_rsi = sum(rsi_values[1:6]) / 5 # Not including the highest RSI for misread issues
    new_row = {'metric_id': 'HJ_AVJ_RSI_Trial_', 'Value': average_rsi}
    cmj_df = pd.concat([cmj_df, pd.DataFrame([new_row])], ignore_index=True)
    # 5.3) IMTP: Take the trial with the highest Peak Vertical Force and upload to df
    imtp_df = pd.read_csv("Output CSVs/Athlete/IMTP.csv")
    imtp_trial_columns = [col for col in imtp_df.columns if col.startswith('trial')]
    peak_values = []
    for trial in imtp_trial_columns:
        peak_values.append(round(float(imtp_df[imtp_df['metric_id'] == "PEAK_VERTICAL_FORCE_Trial_N"][trial].values[0]), 5))
    best_trial = peak_values.index(max(peak_values)) + 1
    rel_value = round(float(imtp_df[imtp_df['metric_id'] == "ISO_BM_REL_FORCE_PEAK_Trial_N/kg"][f'trial {best_trial}'].values[0]), 5)
    new_rows = [{'metric_id': 'IMTP_PEAK_VERTICAL_FORCE_Trial_N', 'Value': peak_values[best_trial - 1]},
                {'metric_id': 'IMTP_ISO_BM_REL_FORCE_PEAK_Trial_N/kg', 'Value': rel_value}]
    cmj_df = pd.concat([cmj_df, pd.DataFrame(new_rows)], ignore_index=True)
    # 5.4) PPU: Take the trial with the best peak concentric force
    ppu_df = pd.read_csv("Output CSVs/Athlete/PPU.csv")
    ppu_trial_columns = [col for col in ppu_df.columns if col.startswith('trial')]
    peak_values = []
    for trial in ppu_trial_columns:
        peak_values.append(round(float(ppu_df[ppu_df['metric_id'] == 'PEAK_CONCENTRIC_FORCE_Trial_N'][trial].values[0]), 5))
    best_trial = peak_values.index(max(peak_values)) + 1
    ppu_df = ppu_df[['metric_id', f'trial {best_trial}']]
    ppu_df.rename(columns={f'trial {best_trial}': 'Value'}, inplace=True)
    ppu_df['metric_id'] = 'PPU_' + ppu_df['metric_id']
    cmj_df = pd.concat([cmj_df, ppu_df], ignore_index=True)
    # CMJ DF now has the best instances of CMJ, HJ, IMTP, and PPU
    # Saving the dataframe to a csv (Outputs/Full Data.csv)
    cmj_df.to_csv("Output CSVs/Athlete/Full_Data.csv")
    

#get_athlete_data("Caden Reese") # Lots of valid test sessions
#get_athlete_data("Charles Gargus") # Full testing battery on July 1st, 2025
#get_athlete_data("Dylan Tostrup") # Full testing battery on July 29th, 2025
# test_date = datetime(2025, 8, 3).date()
# get_athlete_data("Braden Thorn", test_date)

