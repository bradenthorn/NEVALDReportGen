"""Utilities for loading athlete and reference data.

This module centralizes reading the CSV outputs used in the report
generation scripts.  It also provides helpers for refreshing the cached
CSV files by pulling data from VALD or the reference database.  The
``load`` method only reads from existing CSV files; callers that need
fresh data should invoke :meth:`DataLoader.refresh_cache` prior to
calling :meth:`DataLoader.load`.
"""

from __future__ import annotations

import pathlib
from pathlib import Path
import sys
from typing import Dict, Tuple

import pandas as pd

# Allow imports from the project root
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from config import OUTPUT_DIR
from ReportScripts.VALD_API.vald_client import ValdClient
from ReportScripts.VALD_API.ind_ath_data import get_athlete_data
from ReportScripts.PullRefData.pull_all import pull_all_ref


class DataLoader:
    """Load athlete and reference data for report generation."""

    def __init__(self, base_dir: pathlib.Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(OUTPUT_DIR)

    # ------------------------------------------------------------------
    # Cache management
    def refresh_cache(
        self,
        athlete_name: str,
        test_date,
        min_age: int,
        max_age: int,
        client: ValdClient | None = None,
    ) -> None:
        """Refresh the CSV cache files with up-to-date data."""

        if client is None:
            client = ValdClient()

        get_athlete_data(athlete_name, test_date, client)
        pull_all_ref(min_age, max_age)

    # ------------------------------------------------------------------
    # Data loading
    def load(self) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Return athlete data and reference datasets from existing CSV files."""

        athlete_df = pd.read_csv(self.base_dir / "Athlete" / "Full_Data.csv")
        ref_dir = self.base_dir / "Reference"
        ref_data: Dict[str, pd.DataFrame] = {
            "hj": pd.read_csv(ref_dir / "HJ_ref.csv"),
            "imtp": pd.read_csv(ref_dir / "IMTP_ref.csv"),
            "ppu": pd.read_csv(ref_dir / "PPU_ref.csv"),
            "cmj": pd.read_csv(ref_dir / "CMJ_ref.csv"),
        }
        return athlete_df, ref_data


def load_athlete_and_reference_data() -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Convenience wrapper to load athlete and reference data from cache."""

    return DataLoader().load()


def refresh_cache(*args, **kwargs) -> None:
    """Convenience wrapper around :meth:`DataLoader.refresh_cache`."""

    DataLoader().refresh_cache(*args, **kwargs)
