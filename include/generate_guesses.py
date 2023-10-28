from include import database_manager as db_man
import random

users = [["ghornyak", "754392665919062058"],
         ["Korgabor", "529670257573363712"],
         ["venice71", "690169484161712219"],
         ["mvince4","949996915565658144"]]

for player in users:
    uname = player[0]
    u_id = player[1]

    guess = {
        "2023-09-23 22:37:43,596361": {
            "user_name": uname,
            "user_id": u_id,
            "race_id": race_id,
            "race_type": race_type,
            "driver_name": driver_name
        }
    }