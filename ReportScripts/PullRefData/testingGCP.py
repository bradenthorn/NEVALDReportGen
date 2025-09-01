# =================================================================================
# Used this script to test the connection to the GCP BigQuery database
# Confirmed that the connection is working and that the data is being pulled correctly
# This script is not used in the main application, but is kept here for reference
# =================================================================================

import os
from google.cloud import bigquery
from google.oauth2 import service_account

# This path is specific to my local machine, you will need to change it to your own path
# We should find a way to keep this path consistent across machines
# key_path   = "/Users/owenmccandless/VALDReportGenerator/gcp-bq-key.json"

# I think this allows it to run independent of machine as long as the file is named gcp_credentials.json
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
key_path = os.path.join(current_dir, "gcp_credentials.json")
project_id = "vald-ref-data"

# I did change some of this code to test the things I wanted to test - figured this was just a good place to test accessing the ref data
print(f"Looking for credentials at: {key_path}")
print(f"Credentials file exists: {os.path.exists(key_path)}")

try:
    # Load credentials
    creds = service_account.Credentials.from_service_account_file(key_path)
    print("✓ Successfully loaded credentials")
    
    # Create BigQuery client
    client = bigquery.Client(credentials=creds, project=project_id)
    print("✓ Successfully created BigQuery client")
    
    # Test query
    print("Executing test query...")
    df = client.query("""
                      SELECT *
                      FROM `vald-ref-data.athlete_performance_db.imtp_results`
                      LIMIT 5
                      """).result().to_dataframe()
    
    print(f"✓ Query successful! Retrieved {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    if "PEAK_VERTICAL_FORCE_Trial_N" in df.columns:
        avg_peak_force = df["PEAK_VERTICAL_FORCE_Trial_N"].mean()
        print("Average Peak Vertical Force:", avg_peak_force)
    else:
        print("Column 'PEAK_VERTICAL_FORCE_Trial_N' not found in results")
        print("Available columns:", list(df.columns))
        
except FileNotFoundError:
    print(f"❌ Error: Credentials file not found at {key_path}")
    print("Make sure gcp_credentials.json is in the root directory of your project")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print("This might be a permissions issue or the service account might not have access to BigQuery")