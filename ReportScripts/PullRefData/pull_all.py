# =================================================================================
# This script is used to pull all the reference data from the GCP BigQuery database
# This will rely on the independent pull scripts for each test type
# =================================================================================

# -- IMPORTS ----------------------------------------------------------------------
import pathlib
import sys
from pathlib import Path
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
# Add the project root to Python path
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))
# -- IMPORTS FROM OTHER SCRIPTS ---------------------------------------------------
from config import OUTPUT_DIR
from ReportScripts.PullRefData.pull_cmj_ref import pull_cmj_ref
from ReportScripts.PullRefData.pull_hj_ref import pull_hj_ref
from ReportScripts.PullRefData.pull_imtp_ref import pull_imtp_ref
from ReportScripts.PullRefData.pull_ppu_ref import pull_ppu_ref

# -- FUNCTIONS --------------------------------------------------------------------
def pull_all_ref(min_age: int, max_age: int):
    ref_dir = Path(OUTPUT_DIR) / "Reference"
    ref_dir.mkdir(parents=True, exist_ok=True)
    # Step 1: Pull the CMJ reference data (No reference data yet)
    cmj_ref = pull_cmj_ref(min_age, max_age)
    cmj_ref.to_csv(ref_dir / "CMJ_ref.csv")
    # Step 2: Pull the HJ reference data
    hj_ref = pull_hj_ref(min_age, max_age)
    hj_ref.to_csv(ref_dir / "HJ_ref.csv")
    # Step 3: Pull the IMTP reference data
    imtp_ref = pull_imtp_ref(min_age, max_age)
    imtp_ref.to_csv(ref_dir / "IMTP_ref.csv")
    # Step 4: Pull the PPU reference data
    ppu_ref = pull_ppu_ref(min_age, max_age)
    ppu_ref.to_csv(ref_dir / "PPU_ref.csv")

