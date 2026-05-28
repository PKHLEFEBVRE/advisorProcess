"""
Configuration file for the Compliance Tracker.
Update these paths to match the exact locations on your system.
Use the 'r' prefix before the quotes to handle Windows backslashes properly.
"""

MAIN_DIR = r"V:\MONOCLE\Advisor"
# Path where Outlook saves the advisor's .msg emails
EMAILS_DIR = MAIN_DIR + r"\emails"

# Path where the compliance SQLite database should be stored
DB_PATH = MAIN_DIR + r"\compliance.db"

# Path to your Excel model output file
MODEL_FILE = r"V:\MONOCLE\Advisor\advisorProcess\model_output.xlsx"

# Path to your Excel executed trades file
TRADES_FILE = MAIN_DIR + r"\Monocle trades from addin.xlsx"

# Folder where the final PDF Compliance Reports should be saved
REPORTS_DIR = MAIN_DIR + r"\reports"

# The "Named Range" in your Excel model file that contains the data table
MODEL_NAMED_RANGE = "ModelOutput"
