import os
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import pandas as pd
import requests
from dotenv import load_dotenv

from .token_gen import get_vald_token
from .metric_vars import METRICS_OF_INTEREST, unit_map

load_dotenv()

FORCEDECKS_URL = os.getenv("FORCEDECKS_URL")
DYNAMO_URL = os.getenv("DYNAMO_URL")
PROFILE_URL = os.getenv("PROFILE_URL")
TENANT_ID = os.getenv("TENANT_ID")


class ValdClient:
    """Lightweight client for interacting with the VALD Hub API.

    The client manages a :class:`requests.Session` with the generated
    authentication token, caches common responses such as the profile list and
    test sessions, and enforces a simple rate limit between requests to avoid
    overwhelming the API.
    """

    def __init__(self, rate_limit_per_sec: int = 5):
        self.session = requests.Session()
        token = get_vald_token()
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        # Basic token bucket style rate limiting
        self.rate_limit_interval = 1 / rate_limit_per_sec
        self._last_request = 0.0
        # Response caches
        self._profiles_cache: Optional[pd.DataFrame] = None
        self._tests_cache: Dict[Tuple[datetime, str], pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Perform an HTTP request respecting the configured rate limit."""
        elapsed = time.time() - self._last_request
        if elapsed < self.rate_limit_interval:
            time.sleep(self.rate_limit_interval - elapsed)
        response = self.session.request(method, url, **kwargs)
        self._last_request = time.time()
        response.raise_for_status()
        return response

    # ------------------------------------------------------------------
    # Public API methods
    def get_profiles(self) -> pd.DataFrame:
        """Return a DataFrame of profiles, using a cached copy if available."""
        if self._profiles_cache is not None:
            return self._profiles_cache

        url = f"{PROFILE_URL}/profiles?tenantId={TENANT_ID}"
        response = self._request("GET", url)
        df = pd.DataFrame(response.json().get("profiles", []))
        if df.empty:
            return df
        df["givenName"] = df["givenName"].str.strip().str.lower()
        df["familyName"] = df["familyName"].str.strip().str.lower()
        df["fullName"] = (df["givenName"] + " " + df["familyName"]).str.title()
        df = df[["fullName", "profileId"]]
        self._profiles_cache = df
        return df

    def get_tests_by_profile(self, modified_from: datetime, profile_id: str) -> Optional[pd.DataFrame]:
        """Return test sessions for ``profile_id`` since ``modified_from``.

        The response is cached based on the (date, profile) pair.
        """
        cache_key = (modified_from, profile_id)
        if cache_key in self._tests_cache:
            return self._tests_cache[cache_key]

        date_str = modified_from.isoformat()
        url = (
            f"{FORCEDECKS_URL}/tests?TenantId={TENANT_ID}&ModifiedFromUtc={date_str}&ProfileId={profile_id}"
        )
        response = self._request("GET", url)
        df = pd.DataFrame(response.json().get("tests", []))
        if df.empty:
            return None
        df = df[["testId", "modifiedDateUtc", "testType"]]
        df["modifiedDateUtc"] = pd.to_datetime(df["modifiedDateUtc"]).dt.date
        required_tests = {"HJ", "CMJ", "PPU", "IMTP"}
        test_types_per_date = df.groupby("modifiedDateUtc")["testType"].agg(set)
        valid_dates = test_types_per_date[test_types_per_date.apply(lambda x: required_tests.issubset(x))].index
        filtered_df = df[df["modifiedDateUtc"].isin(valid_dates)]
        if filtered_df.empty:
            return None
        self._tests_cache[cache_key] = filtered_df
        return filtered_df

    def get_fd_results(self, test_id: str, test_type: str) -> Optional[pd.DataFrame]:
        """Fetch ForceDecks results for a specific test session."""
        url = f"{FORCEDECKS_URL}/v2019q3/teams/{TENANT_ID}/tests/{test_id}/trials"
        response = self._request("GET", url)
        test_data_json = response.json()
        if not test_data_json or not isinstance(test_data_json, list):
            return None

        all_results = []
        for trial in test_data_json:
            for res in trial.get("results", []):
                all_results.append(
                    {
                        "value": res.get("value"),
                        "limb": res.get("limb"),
                        "result_key": res["definition"].get("result", ""),
                        "unit": res["definition"].get("unit", ""),
                    }
                )
        if not all_results:
            return None

        df = pd.DataFrame(all_results)
        df["unit"] = df["unit"].apply(unit_map)
        df["metric_id"] = (
            df["result_key"].astype(str)
            + "_"
            + df["limb"].astype(str)
            + "_"
            + df["unit"].astype(str)
        )
        df["trial"] = df.groupby("metric_id").cumcount() + 1
        pivot = df.pivot_table(index="metric_id", columns="trial", values="value", aggfunc="first")
        pivot.columns = [f"trial {c}" for c in pivot.columns]
        pivot = pivot.reset_index()
        pivot = pivot[pivot["metric_id"].isin(METRICS_OF_INTEREST[test_type])]

        return pivot