# =================================================================================
# Pull athlete data from VALD Hub and return a DataFrame of best trials.
#
# The process is:
# 1.) Authentication - Obtain VALD access token (using environment credentials)
# 2.) Fetch all profiles - map names to IDs
# 3.) Fetch athlete test sessions - find sessions containing all four tests
# 4.) Fetch test session data - retrieve all trial data for the session
# 5.) Select best trials and assemble a DataFrame for report generation
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
from datetime import datetime
import pandas as pd

from typing import Optional
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------

from nevald_report_gen.api.vald_client import ValdClient
from nevald_report_gen.api.VALDapiHelpers import cmj_z_score

def select_best_cmj_trial(df: pd.DataFrame) -> pd.DataFrame:
    """Return CMJ metrics for the best trial based on z-score."""
    trial_columns = [col for col in df.columns if col.startswith("trial")]
    z_scores = []
    for trial in trial_columns:
        trial_score = cmj_z_score(
            pd.to_numeric(df[df["metric_id"] == "CONCENTRIC_IMPULSE_Trial_Ns"][trial].values[0]),
            pd.to_numeric(df[df["metric_id"] == "ECCENTRIC_BRAKING_RFD_Trial_N/s"][trial].values[0]),
            pd.to_numeric(df[df["metric_id"] == "PEAK_CONCENTRIC_FORCE_Trial_N"][trial].values[0]),
            pd.to_numeric(
                df[df["metric_id"] == "BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg"][trial].values[0]
            ),
            pd.to_numeric(df[df["metric_id"] == "RSI_MODIFIED_Trial_RSI_mod"][trial].values[0]),
            pd.to_numeric(df[df["metric_id"] == "ECCENTRIC_BRAKING_IMPULSE_Trial_Ns"][trial].values[0]),
        )
        z_scores.append(round(float(trial_score), 5))
    best_trial = z_scores.index(max(z_scores)) + 1
    best_df = df[["metric_id", f"trial {best_trial}"]].copy()
    best_df["metric_id"] = "CMJ_" + best_df["metric_id"]
    best_df.rename(columns={f"trial {best_trial}": "Value"}, inplace=True)
    return best_df


def select_best_hj_trial(df: pd.DataFrame) -> pd.DataFrame:
    """Return a dataframe with averaged RSI values for HJ."""
    trial_columns = [col for col in df.columns if col.startswith("trial")]
    rsi_values = [
        round(float(df[df["metric_id"] == "HOP_RSI_Trial_"][trial].values[0]), 5)
        for trial in trial_columns
    ]
    rsi_values.sort(reverse=True)
    average_rsi = sum(rsi_values[1:6]) / 5
    return pd.DataFrame([
        {"metric_id": "HJ_AVJ_RSI_Trial_", "Value": average_rsi}
    ])


def select_best_imtp_trial(df: pd.DataFrame) -> pd.DataFrame:
    """Return IMTP metrics for the trial with highest peak vertical force."""
    trial_columns = [col for col in df.columns if col.startswith("trial")]
    peak_values = [
        round(float(df[df["metric_id"] == "PEAK_VERTICAL_FORCE_Trial_N"][trial].values[0]), 5)
        for trial in trial_columns
    ]
    best_trial = peak_values.index(max(peak_values)) + 1
    rel_value = round(
        float(
            df[df["metric_id"] == "ISO_BM_REL_FORCE_PEAK_Trial_N/kg"][f"trial {best_trial}"].values[0]
        ),
        5,
    )
    rows = [
        {"metric_id": "IMTP_PEAK_VERTICAL_FORCE_Trial_N", "Value": peak_values[best_trial - 1]},
        {"metric_id": "IMTP_ISO_BM_REL_FORCE_PEAK_Trial_N/kg", "Value": rel_value},
    ]
    return pd.DataFrame(rows)


def select_best_ppu_trial(df: pd.DataFrame) -> pd.DataFrame:
    """Return PPU metrics for the trial with highest peak concentric force."""
    trial_columns = [col for col in df.columns if col.startswith("trial")]
    peak_values = [
        round(float(df[df["metric_id"] == "PEAK_CONCENTRIC_FORCE_Trial_N"][trial].values[0]), 5)
        for trial in trial_columns
    ]
    best_trial = peak_values.index(max(peak_values)) + 1
    best_df = df[["metric_id", f"trial {best_trial}"]].copy()
    best_df.rename(columns={f"trial {best_trial}": "Value"}, inplace=True)
    best_df["metric_id"] = "PPU_" + best_df["metric_id"]
    return best_df


# -- FUNCTIONS --------------------------------------------------------------------
def get_athlete_data(
    athlete_name: str,
    test_date: datetime,
    client: Optional[ValdClient] = None,
):
    """Pull athlete data for the specified test date and return it as a DataFrame."""
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
    results = {}
    for testType, testID in test_IDandType_list:
        df = client.get_fd_results(testID, testType)
        if df is not None:
            results[testType] = df

    # Step 5: Select best trials and merge data
    _cmj_df = select_best_cmj_trial(results["CMJ"])
    _hj_df = select_best_hj_trial(results["HJ"])
    _imtp_df = select_best_imtp_trial(results["IMTP"])
    _ppu_df = select_best_ppu_trial(results["PPU"])

    full_df = pd.concat([_cmj_df, _hj_df, _imtp_df, _ppu_df], ignore_index=True)
    full_df.iloc[1, 1] = full_df.iloc[1, 1] * 2.20462
    return full_df
