"""
Configuration file for the Compliance Tracker.
Update these paths to match the exact locations on your system.
Use the 'r' prefix before the quotes to handle Windows backslashes properly.
"""

# Path where Outlook saves the advisor's .msg emails
EMAILS_DIR = r"C:\Users\plefebvre\Documents\advisorProcess\emails"

# Path where the compliance SQLite database should be stored
DB_PATH = r"V:\MONOCLE\Advisor\advisorProcess\compliance.db"

# Path to your Excel model output file
MODEL_FILE = r"V:\MONOCLE\Advisor\advisorProcess\model_output.xlsx"

# Path to your Excel executed trades file
TRADES_FILE = r"V:\MONOCLE\Advisor\advisorProcess\trades.xlsx"

# Folder where the final PDF Compliance Reports should be saved
REPORTS_DIR = r"V:\MONOCLE\Advisor\advisorProcess\reports"
