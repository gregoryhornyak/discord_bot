import json

# paths

UPCOMING_DATE_PATH =    "resources/data/upcoming_date"
PREV_GPS_DETAILS_PATH =  "resources/data/prev_gps_details.json"
NEXT_GP_DETAILS_PATH =  "resources/data/next_gp_details.json"
NEXT_GP_DRIVERS_INFO_PATH =  "resources/data/next_gp_drivers_info.json"
NEXT_GP_CATEGORIES_PATH =    "resources/data/next_gp_categories.json"
FETCH_LOG_PATH =          "resources/data/fetch_log.json"
YEAR_SCHEDULE_PATH =      "resources/data/whole_year_gp_dates.json"
TOKEN_PATH =        "resources/token/token"
PASSW_PATH =        "resources/password/passw"
UPLOADS_PATH =      "resources/uploads/"
USER_GUESS_HISTORY_PATH =        "resources/uploads/user_guess_history.md"
USER_GUESS_HISTORY_PDF_PATH =    "resources/uploads/user_guess_history"
USER_POINT_HISTORY_PATH =        "resources/uploads/user_point_history.md"
USER_POINT_HISTORY_PDF_PATH =    "resources/uploads/user_point_history"
REPORT_PATH =       "resources/uploads/report.md"
REPORT_PDF_PATH =   "resources/uploads/report"
GUESS_DB_PATH =     "resources/inventory/guess_db.json"
SCORE_TABLE_PATH =  "resources/inventory/score_table.json"
USERS_DB_PATH =     "resources/inventory/users_db.json"
LOGS_PATH =                 "resources/logs/botlogs.log"
BOT_LOGS_EXT_MD_PATH =      "resources/logs/botlogs_extract.md"
BOT_LOGS_EXT_PDF_PATH =     "resources/logs/botlogs_extract.pdf"
MANIFEST_PATH =      "docs/manifest/manifest.json"
PROFILE_PICS_PATH =  "resources/uploads/"
STATE_FILE_PATH =    "resources/config/state.json"
TEST_DATA_PATH =     "resources/tests/test_data.json"

SERVER_CHANNEL_ID_PATH = "resources/config/discord_info.json"

# time delays

ALERT_CHECK_DELAY = 55

# messages

BOT_SHUTDOWN_UPGRD_MESSAGE = "Bot is shutting down and will be upgraded..."
BOT_START_DETAILS_MESSAGE = f"bot_name\n\
vversion [latest:latest_ver]\n\
is now running...\n\
Latest update: latest_update"

BOT_START_DETAILS_MESSAGE_LINE = "Latest update"
BOT_START_SHORT_MESSAGE = "Bot is on"

BOT_STATE = "STABLE" # TEST | ALPHA | STABLE

BLACK_LISTED_PHRASES = ["Ne káromkodjál, mert pofán baszlak!",
                 "Még egy ilyen és szájba kúrlak!",
                 "De szépen beszélsz, a rohadt életbe!",
                 "Ki tanított ilyen kurva rondán beszélni?"]

SWEAR_WORDS = ["fasz", "bazd", "geci", "kurva", "baszki", "segg", "pina", "anyád", "szar", "buzi", "cigány", "cibbon"]
GRATULATION_PHRASES = ["Bravo","Kudos","Superb"]

# date formats

LONG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

# header names

CATEGORY =      "category" # grand prix guess categories
DRIVER =        "driver" # driver / dnf value
USERNAME =      "user_name" # user name
USER_ID =       "user_id" # user id
RESULT =        "result" # result of grand prix category
GP_ID =         "gp_id" # id of grand prix
GP_NAME =       "gp_name"
GUESS =         "guess" # the guess value
SCORE =         "score" # the score for the category
