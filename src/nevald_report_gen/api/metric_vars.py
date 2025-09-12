# =================================================================================
# This script is used to hold a few long lists/functions to keep other scripts clean
# Ideally this also makes it easier to change metrics in the future
# Includes: Unit conversions, important metrics, etc.
# =================================================================================

# -- UNIT CONVERSIONS --------------------------------------------------------------
def unit_map(unit: str) -> str:
    _map = {
        'Centimeter':                       'cm',
        'Inch':                             'in',
        'Joule':                            'J',
        'Kilo':                             'kg',
        'Meter Per Second':                 'm/s',
        'Meter Per Second Per Second':     'm/s²',
        'Millisecond':                      'ms',
        'Second':                           's',
        'Newton':                           'N',
        'Newton Per Centimeter':            'N/cm',
        'Newton Per Kilo':                  'N/kg',
        'Newton Per Meter':                 'N/m',
        'Newton Per Second':                'N/s',
        'Newton Per Second Per Centimeter': 'N/s/cm',
        'Newton Per Second Per Kilo':       'N/s/kg',
        'Newton Second':                    'Ns',
        'Newton Second Per Kilo':           'Ns/kg',
        'Watt':                             'W',
        'Watt Per Kilo':                    'W/kg',
        'Watt Per Second':                  'W/s',
        'Watt Per Second Per Kilo':         'W/s/kg',
        'Joule':                            'J',
        'Percent':                          '%',
        'Pound':                            'lb',
        'RSIModified':                      'RSI_mod',
        'No Unit':                          '',
    }
    return _map.get(unit, unit)

# -- METRICS OF INTEREST -----------------------------------------------------------
METRICS_OF_INTEREST = {
    'CMJ': ['BODY_WEIGHT_LBS_Trial_lb',
            'CONCENTRIC_DURATION_Trial_ms',
            'CONCENTRIC_IMPULSE_Trial_Ns',
            'CONCENTRIC_IMPULSE_Asym_Ns',
            'CONCENTRIC_RFD_Trial_N/s',
            'ECCENTRIC_BRAKING_IMPULSE_Asym_Ns',
            'ECCENTRIC_BRAKING_RFD_Trial_N/s',
            'JUMP_HEIGHT_IMP_MOM_Trial_cm',
            'PEAK_CONCENTRIC_FORCE_Trial_N',
            'RSI_MODIFIED_IMP_MOM_Trial_RSI_mod',
            'RSI_MODIFIED_Trial_RSI_mod',
            'PEAK_TAKEOFF_POWER_Trial_W',
            'BODYMASS_RELATIVE_TAKEOFF_POWER_Trial_W/kg',
            'CON_P2_CON_P1_IMPULSE_RATIO_Trial_',
            'CONCENTRIC_IMPULSE_P1_Trial_Ns',
            'CONCENTRIC_IMPULSE_P2_Trial_Ns',
            'CONCENTRIC_IMPULSE_P1_Asym_Ns',
            'CONCENTRIC_IMPULSE_P2_Asym_Ns',
            'ECCENTRIC_BRAKING_IMPULSE_Trial_Ns',],
    'IMTP': ['ISO_BM_REL_FORCE_PEAK_Trial_N/kg',
             'PEAK_VERTICAL_FORCE_Trial_N'],
    'PPU': ['ECCENTRIC_BRAKING_RFD_Trial_N/s',
            'MEAN_ECCENTRIC_FORCE_Asym_N',
            'MEAN_TAKEOFF_FORCE_Asym_N',
            'PEAK_CONCENTRIC_FORCE_Trial_N',
            'RELATIVE_PEAK_CONCENTRIC_FORCE_Trial_N/kg',
            'CONCENTRIC_DURATION_Trial_ms',
            'PEAK_CONCENTRIC_FORCE_Asym_N',
            'PEAK_ECCENTRIC_FORCE_Asym_N'], 
    'HJ': ['HOP_RSI_Trial_']
}