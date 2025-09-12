import pandas as pd

from nevald_report_gen.api.ind_ath_data import (
    select_best_cmj_trial,
    select_best_hj_trial,
    select_best_imtp_trial,
    select_best_ppu_trial,
)


def test_select_best_cmj_trial():
    df = pd.DataFrame(
        {
            "metric_id": [
                "CONCENTRIC_IMPULSE_Trial_Ns",
                "ECCENTRIC_BRAKING_RFD_Trial_N/s",
                "PEAK_CONCENTRIC_FORCE_Trial_N",
                "BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg",
                "RSI_MODIFIED_Trial_RSI_mod",
                "ECCENTRIC_BRAKING_IMPULSE_Trial_Ns",
            ],
            "trial 1": [1, 1, 1, 1, 1, 1],
            "trial 2": [10, 10, 10, 10, 10, 10],
        }
    )
    result = select_best_cmj_trial(df)
    expected = pd.DataFrame(
        {
            "metric_id": [
                "CMJ_CONCENTRIC_IMPULSE_Trial_Ns",
                "CMJ_ECCENTRIC_BRAKING_RFD_Trial_N/s",
                "CMJ_PEAK_CONCENTRIC_FORCE_Trial_N",
                "CMJ_BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg",
                "CMJ_RSI_MODIFIED_Trial_RSI_mod",
                "CMJ_ECCENTRIC_BRAKING_IMPULSE_Trial_Ns",
            ],
            "Value": [10, 10, 10, 10, 10, 10],
        }
    )
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected)


def test_select_best_hj_trial():
    df = pd.DataFrame(
        {
            "metric_id": ["HOP_RSI_Trial_"],
            "trial 1": [1],
            "trial 2": [2],
            "trial 3": [3],
            "trial 4": [4],
            "trial 5": [5],
            "trial 6": [6],
        }
    )
    result = select_best_hj_trial(df)
    expected = pd.DataFrame(
        [{"metric_id": "HJ_AVJ_RSI_Trial_", "Value": 3.0}]
    )
    pd.testing.assert_frame_equal(result, expected)


def test_select_best_imtp_trial():
    df = pd.DataFrame(
        {
            "metric_id": [
                "PEAK_VERTICAL_FORCE_Trial_N",
                "ISO_BM_REL_FORCE_PEAK_Trial_N/kg",
            ],
            "trial 1": [100, 1.5],
            "trial 2": [200, 2.5],
        }
    )
    result = select_best_imtp_trial(df)
    expected = pd.DataFrame(
        [
            {"metric_id": "IMTP_PEAK_VERTICAL_FORCE_Trial_N", "Value": 200},
            {"metric_id": "IMTP_ISO_BM_REL_FORCE_PEAK_Trial_N/kg", "Value": 2.5},
        ]
    )
    pd.testing.assert_frame_equal(result, expected)


def test_select_best_ppu_trial():
    df = pd.DataFrame(
        {
            "metric_id": [
                "PEAK_CONCENTRIC_FORCE_Trial_N",
                "OTHER_METRIC_Trial_N",
            ],
            "trial 1": [1000, 10],
            "trial 2": [2000, 20],
        }
    )
    result = select_best_ppu_trial(df)
    expected = pd.DataFrame(
        {
            "metric_id": [
                "PPU_PEAK_CONCENTRIC_FORCE_Trial_N",
                "PPU_OTHER_METRIC_Trial_N",
            ],
            "Value": [2000, 20],
        }
    )
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected)
