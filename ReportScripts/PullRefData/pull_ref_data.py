from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from pathlib import Path
import sys

# Add project root to path to import config
sys.path.append(str(Path(__file__).parent.parent.parent))
from config import GCP_CREDENTIALS_PATH, GCP_PROJECT_ID


def pull_ref(test_type: str, min_age: int, max_age: int) -> pd.DataFrame:
    """Pull reference data for a specific test type.

    Parameters
    ----------
    test_type : str
        Fully qualified table name of the reference data.
    min_age : int
        Minimum athlete age to include.
    max_age : int
        Maximum athlete age to include.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the requested reference data.
    """
    # Connect to BigQuery
    creds = service_account.Credentials.from_service_account_file(GCP_CREDENTIALS_PATH)
    client = bigquery.Client(credentials=creds, project=GCP_PROJECT_ID)

    # Build and run query
    sql = f"""
        SELECT *
        FROM `{test_type}`
        WHERE age_at_test BETWEEN @min_age AND @max_age
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_age", "INT64", min_age),
            bigquery.ScalarQueryParameter("max_age", "INT64", max_age),
        ]
    )
    query_job = client.query(sql, job_config=job_config)
    return query_job.result().to_dataframe()