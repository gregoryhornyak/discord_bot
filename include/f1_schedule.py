import fastf1
import datetime

PATH = 'resources/'
CACHE_DIR = 'resources/f1_cache/'

def get_present(as_str=False):
    if as_str:
        return str(datetime.datetime.now())
    return datetime.datetime.now()

def match_dates(target_date):
    today = get_present()
    #print(f"{target_date = }")
    if today > target_date[1]:
        return False
    return True

def get_session_dates(session_type=1): # doesnt matter if string or not
    # for 2023:
    # 1: FP1
    # 2: Q
    # 3: FP2
    # 4: SPRINT
    # 5: Race
    fastf1.Cache.enable_cache(CACHE_DIR)
    current_year = int(str(datetime.datetime.today().year))
    session_dates = [fastf1.get_session(current_year, r, session_type).date for r in range(1,24)]
    return session_dates

def get_future_sessions():
    """return every future session date"""
    future_dates = filter(match_dates,get_sessions_with_ids())
    future_dates = list(future_dates)
    return future_dates

def get_last_session_results():
    fastf1.Cache.enable_cache(CACHE_DIR)
    current_year = int(str(datetime.datetime.today().year))
    session_dates = get_future_sessions()
    sess = fastf1.get_session(current_year,session_dates[0][0]-1,'R')
    sess_loaded = sess.load()
    results = sess.results
    date = sess.date
    #print(f"On {date}:\n{results[['BroadcastName', 'Points']].iloc[:3]} points")
    return results[['BroadcastName', 'Points']].iloc[:3]

def get_custom_session_results(year,event_id,sess_type):
    fastf1.Cache.enable_cache(CACHE_DIR)
    sess = fastf1.get_session(year,event_id,sess_type)
    sess_loaded = sess.load() # usually fails to load Free Practice Data
    results = sess.results 
    print(f"{year = }\n{event_id = }\n{results.iloc[:5]} points")
    return results
    

def get_session_drivers():
    """
    returns driver names and their team names
    """
    fastf1.Cache.enable_cache(CACHE_DIR)
    current_year = int(str(datetime.datetime.today().year))
    sess = fastf1.get_session(current_year,3,'R')
    sess_loaded = sess.load()
    driver_names = [sess.get_driver(str(id))['BroadcastName'].split(" ",1)[1] for id in sess.drivers]
    driver_team = [sess.get_driver(str(id))['TeamName'] for id in sess.drivers]
    return driver_names, driver_team
    
def get_sessions_with_ids():
    """returns every session in a year"""
    session_dates = get_session_dates() # get session dates
    event_id_list = [id+1 for id in range(len(session_dates))] # serial numbers from 1 to 23
    sessions = list(zip(event_id_list,session_dates)) # merge them into a list of tuples
    return sessions

if __name__ == "__main__":
    print("\nLOCAL TEST:\n\n")
    res = get_custom_session_results(2022,4,3)
    with open("results.txt","w") as f:
        f.write(res.to_string())