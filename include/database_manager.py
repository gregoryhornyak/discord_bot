from include.logging_manager import logger
from include.constants import * # json
import datetime

def create_single_user_db(user_id,user_name):
    """checks json empty | if user in | adds user to db"""
    users_db = {}
    def populate_json(_user_name=user_name):
        return {
            "user_name": _user_name,
            "round_score": {},
            "total_points": 0
        }
    try:
        with open(f"{INVENTORY_PATH}users_db.json","r") as f:
            users_db = json.load(f)
    except FileNotFoundError:
        logger.error("No guess_db found")
    except json.decoder.JSONDecodeError:
        logger.info(f"empty json file")
        users_db[user_id] = populate_json()
    else:
        # check if user already in db -> if not create entry
        if users_db.get(user_id) is None:
            users_db[user_id] = populate_json()
    finally:
        with open(f"{INVENTORY_PATH}users_db.json","w") as f:
            json.dump(users_db,f,indent=4)

def save_guess(name,id,select_race,select_driver,next_race_id,dnf=False):
    guess_db = {}
    present = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")
    def populate_json(_name=name,_id=id,_select_race=select_race,_select_driver=select_driver,_next_race_id=next_race_id,_dnf=dnf):
        if _dnf:
            return {
            "user_name": _name,
            "user_id": str(_id),
            "race_id": _next_race_id,
            "race_type": _select_race,
            "driver_name": str(_select_driver)
        }
        else:
            return {
            "user_name": _name,
            "user_id": str(_id),
            "race_id": _next_race_id,
            "race_type": _select_race.values[0],
            "driver_name": _select_driver.values[0]
        }
    if dnf:
        logger.info(f"{name},{select_race},{select_driver}")
    else:
        logger.info(f"{name},{select_race.values[0]},{select_driver.values[0]}")

    try:
        with open(f"{INVENTORY_PATH}guess_db.json", "r") as f:
            guess_db = json.load(f)
    except FileNotFoundError:
        logger.error("No guess_db found")
        guess_db[present] = populate_json()
    except json.decoder.JSONDecodeError:
        logger.info("Empty json file")
        guess_db[present] = populate_json()
    else:
        if guess_db.get(present) is None:
            guess_db[present] = populate_json()
    finally:
        logger.info("Guess_db updated")
        with open(f"{INVENTORY_PATH}guess_db.json", "w") as f:
            json.dump(guess_db, f, indent=4)
        logger.info("Guess saved")
        
def check_load_json(path):
    try:
        with open(path, "r") as f:
            json_file = json.load(f)
    except FileNotFoundError:
        logger.error(f"{path}: Missing File")
        with open(path, "w") as f:
            json.dump(f,{},indent=4)
    except json.decoder.JSONDecodeError:
        logger.error(f"{path}: Empty Json File")
        # populate file with JSON data
    else:
        return json_file
    finally:
        return False
        