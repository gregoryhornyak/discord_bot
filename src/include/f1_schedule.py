import fastf1
import datetime

CACHE_DIR = '../src/databases'

def get_present(as_str=False):
    if as_str:
        return str(datetime.datetime.now())
    return datetime.datetime.now()

def match_dates(target_date):
    today = get_present()
    #print(f'{today = } | {d = }')
    if today > target_date:
        return False
    return True

def get_session_dates():
    fastf1.Cache.enable_cache(CACHE_DIR)
    current_year = int(str(datetime.datetime.today().year))
    session_dates = [fastf1.get_session(current_year, r, 'R').date for r in range(1,24)]
    return session_dates

def get_future_sessions():
    """return every future session date"""
    future_dates = filter(match_dates,get_session_dates())
    future_dates = [f for f in future_dates]
    return future_dates

def get_session_drivers():
    fastf1.Cache.enable_cache(CACHE_DIR)
    current_year = int(str(datetime.datetime.today().year))
    sess = fastf1.get_session(current_year,3,'R')
    sess_loaded = sess.load()
    driver_names = [sess.get_driver(str(id))['BroadcastName'].split(" ",1)[1] for id in sess.drivers]
    return driver_names
    
def get_sessions_with_ids():
    session_dates = get_session_dates() # get session dates
    event_id_list = [id+1 for id in range(len(session_dates))] # serial numbers from 1 to 23
    sessions = list(zip(event_id_list,session_dates)) # merge them into a list of tuples
    return sessions

if __name__ == "__main__":
    print("\nLOCAL TEST:\n\n")
