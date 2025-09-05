"""Utilities for loading athlete and reference data.

This module centralizes reading the CSV outputs used in the report
generation scripts.  It also encapsulates the logic for optionally
refreshing the cached CSV files by pulling data from VALD or the
reference database.
"""

from __future__ import annotations

import pathlib
import sys
from typing import Dict, Tuple

import pandas as pd

# Allow imports from the project root
project_root = pathlib.Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from ReportScripts.VALD_API.vald_client import ValdClient
from ReportScripts.VALD_API.ind_ath_data import get_athlete_data
from ReportScripts.PullRefData.pull_all import pull_all_ref


class DataLoader:
    """Load athlete and reference data for report generation."""

    def __init__(self, base_dir: pathlib.Path | None = None) -> None:
        self.base_dir = base_dir or project_root / "Output CSVs"

    def load(
        self,
        athlete_name: str,
        test_date,
        min_age: int,
        max_age: int,
        use_cached_data: bool = False,
        client: ValdClient | None = None,
    ) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Return athlete data and reference datasets.

        Parameters
        ----------
        athlete_name: str
            Name of the athlete whose data should be loaded.
        test_date: datetime.date
            Date of the test for the athlete.
        min_age, max_age: int
            Age range for pulling reference data when refreshing caches.
        use_cached_data: bool
            If ``False`` the underlying CSV files are refreshed using
            ``get_athlete_data`` and ``pull_all_ref`` before being read.
        client: ValdClient | None
            Optional VALD client used when refreshing the athlete data.
        """

        if not use_cached_data:
            if client is None:
                client = ValdClient()
            # Update the CSV cache files
            get_athlete_data(athlete_name, test_date, client)
            pull_all_ref(min_age, max_age)

        athlete_df = pd.read_csv(self.base_dir / "Athlete" / "Full_Data.csv")
        ref_dir = self.base_dir / "Reference"
        ref_data: Dict[str, pd.DataFrame] = {
            "hj": pd.read_csv(ref_dir / "HJ_ref.csv"),
            "imtp": pd.read_csv(ref_dir / "IMTP_ref.csv"),
            "ppu": pd.read_csv(ref_dir / "PPU_ref.csv"),
            "cmj": pd.read_csv(ref_dir / "CMJ_ref.csv"),
        }
        return athlete_df, ref_data


def load_athlete_and_reference_data(*args, **kwargs):
    """Convenience wrapper around :class:`DataLoader`."""
    return DataLoader().load(*args, **kwargs)

