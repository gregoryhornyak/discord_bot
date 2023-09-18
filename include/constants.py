import json

UPCOMING_DATE_PATH = "resources/data/"
SCORE_TABLE_PATH = "resources/data/"
TOKEN_PATH = "resources/token/"
PASSW_PATH = "resources/passw/"
UPLOADS_PATH = "resources/uploads/"
GUESS_FILE = "resources/data/"
SCORES_FILE = "resources/scores/"
USER_SCORES = "resources/data/"
INVENTORY_PATH = "resources/inventory/"
LOGS_PATH = "resources/logs/"
MANIFEST_PATH = "docs/manifest/"
SCORE_TABLE_PATH = "resources/inventory/"

with open(f"{INVENTORY_PATH}score_table.json") as f:
    score_table = json.load(f)

F1_RACE_TYPES = [key for key in score_table.keys()]

CHANNEL_ID = 1078427611597906004