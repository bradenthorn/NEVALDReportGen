# =================================================================================
# This script is used to calculate the composite score for an athlete
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import pathlib
import sys
import pandas as pd
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# -- FUNCTIONS --------------------------------------------------------------------
def calculate_composite_score():
    # 1.0) Read in the reference data
    cmj_ref = pd.read_csv("Output CSVs/Reference/CMJ_ref.csv")
    hj_ref = pd.read_csv("Output CSVs/Reference/HJ_ref.csv")
    imtp_ref = pd.read_csv("Output CSVs/Reference/IMTP_ref.csv")
    ppu_ref = pd.read_csv("Output CSVs/Reference/PPU_ref.csv")
    # 1.0.1) Clean the individual reference data
    cmj_ref = cmj_ref[['athlete_name', 'BODY_WEIGHT_LBS_Trial_lb', 'PEAK_TAKEOFF_POWER_Trial_W', 
                       'CONCENTRIC_IMPULSE_Trial_Ns', 'ECCENTRIC_BRAKING_IMPULSE_Trial_Ns']]
    hj_ref = hj_ref[['athlete_name', 'hop_rsi_avg_best_5']]
    imtp_ref = imtp_ref[['athlete_name', 'PEAK_VERTICAL_FORCE_Trial_N']]
    ppu_ref = ppu_ref[['athlete_name', 'PEAK_CONCENTRIC_FORCE_Trial_N']]
    # 1.0.1) Merge the reference data
    comp_ref = cmj_ref.merge(hj_ref, on='athlete_name')
    comp_ref = comp_ref.merge(imtp_ref, on='athlete_name')
    comp_ref = comp_ref.merge(ppu_ref, on='athlete_name')
    # This would be the point where we would figure out Composite Score
    
    print(comp_ref)

calculate_composite_score()