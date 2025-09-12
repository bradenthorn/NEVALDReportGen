"""Utilities for loading athlete and reference data.

This module fetches data directly from the VALD Hub API and the
reference database, returning populated DataFrames without writing any
intermediate CSV files to disk.
"""

from __future__ import annotations

import pathlib
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd


from nevald_report_gen.config import OUTPUT_DIR
from nevald_report_gen.api.vald_client import ValdClient
from nevald_report_gen.api.ind_ath_data import get_athlete_data
from nevald_report_gen.data.pull_all import pull_all_ref


class DataLoader:
    """Load athlete and reference data for report generation."""

    def __init__(self, base_dir: pathlib.Path | None = None) -> None:
        # ``base_dir`` is retained only for backwards compatibility with tests
        self.base_dir = Path(base_dir) if base_dir else Path(OUTPUT_DIR)

    def load(
        self,
        athlete_name: str,
        test_date,
        min_age: int,
        max_age: int,
        client: ValdClient | None = None,
    ) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
        """Fetch athlete and reference data and return them in memory."""

        if client is None:
            client = ValdClient()

        athlete_df = get_athlete_data(athlete_name, test_date, client)
        ref_data = pull_all_ref(min_age, max_age)
        return athlete_df, ref_data


def load_athlete_and_reference_data(
    athlete_name: str,
    test_date,
    min_age: int,
    max_age: int,
    client: ValdClient | None = None,
) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """Convenience wrapper to load athlete and reference data."""

    return DataLoader().load(athlete_name, test_date, min_age, max_age, client)
