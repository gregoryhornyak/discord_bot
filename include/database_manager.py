from include.logging_manager import logger
from include.constants import * # json
import datetime
import random

def save_guess(name,id,select_race,select_driver,next_race_id,dnf=False):
    guess_db = {}
    now_string = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")
    ran_hour = random.randint(10,23)
    ran_minute = random.randint(10,50)
    ran_milisec = random.randint(100000,900000)
    present = now_string if BOT_STATE != "TEST" else f"2023-11-23 {ran_hour}:{ran_minute}:30,{ran_milisec}"
    # dnf is driver_name
    def populate_json(_name=name,_id=id,_select_race=select_race,_select_driver=select_driver,_next_race_id=next_race_id,_dnf=dnf):
        _next_race_id = _next_race_id if BOT_STATE != "TEST" else "1226"
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
            "race_type": _select_race,
            "driver_name": _select_driver
        }

    try:
        with open(f"{GUESS_DB_PATH}", "r") as f:
            guess_db = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
        logger.error(e)
        guess_db[present] = populate_json()
    else:
        if guess_db.get(present) is None:
            guess_db[present] = populate_json()
    finally:
        logger.info("Guess saved")
        with open(f"{GUESS_DB_PATH}", "w") as f:
            json.dump(guess_db, f, indent=4)
        logger.info("Guess_db updated")
        
        
        