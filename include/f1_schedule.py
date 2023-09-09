import fastf1
import datetime
#import pandas

PATH = 'resources/'
CACHE_DIR = 'resources/f1_cache/'

# HINT: only use either datetime.today or datetime.now
# currently using .now() 


def get_present() -> datetime.datetime:
    """returns present date and time"""
    """
    datetime.datetime.now() ->
    datetime.datetime(2023, 5, 17, 17, 37, 15, 273839)
    .year, .day, .minute, .microsecond
    """
    return datetime.datetime.now()

def match_dates(target_date: datetime.datetime) -> bool:
    today = get_present()
    if today <= target_date[1]:
        return True
    return False

def fetch_data(CACHE_DIR=CACHE_DIR):
    fastf1.Cache.enable_cache(CACHE_DIR)

def get_session_dates(session_type=5) -> list:
    # for 2023:
    # 1: FP1
    # 2: Q
    # 3: FP2
    # 4: SPRINT
    # 5: Race
    fetch_data()
    current_year = get_present().year
    #print(f"{current_year = }, {session_type = }")
    session_dates = [fastf1.get_session(current_year, r, session_type).date for r in range(1,23)]
    return session_dates

def get_sessions_with_ids() -> list:
    """returns every session in a year with its ID"""
    session_dates = get_session_dates() # get session dates
    event_id_list = [id+1 for id in range(len(session_dates))] # serial numbers from 1 to 23
    sessions_with_ids = list(zip(event_id_list,session_dates)) # merge them into a list of tuples
    return sessions_with_ids

def get_future_sessions() -> list:
    """return every future (and present) session date with their id"""
    future_dates = filter(match_dates,get_sessions_with_ids())
    future_dates = list(future_dates)
    return future_dates

def get_last_session_results(race_type=5,back=0):
    """returns table, last_id, last_date"""
    fetch_data()
    current_year = get_present().year
    session_dates = get_future_sessions() # to get the current id
    last_session_id = session_dates[0][0]-1-back
    sess = fastf1.get_session(current_year,last_session_id,race_type) # fix get_future_sess to include current session
    sess_loaded = sess.load()
    results = sess.results
    last_session_date = fastf1.get_session(current_year,last_session_id,race_type).date

    # issue: printing the results is chaotic as the table doesnt look pretty
    # > solution: create md file, create image then upload
    return results.iloc[:3], last_session_id, last_session_date  # without trimming message body too big

def get_custom_session_results(year,event_id,sess_type):
    fetch_data()
    sess = fastf1.get_session(year,event_id,sess_type)
    sess_loaded = sess.load() # usually fails to load Free Practice Data
    results = sess.results 
    #print(f"{year = }\n{event_id = }\n{results.iloc[:5]} points")
    return results

def get_session_drivers() -> list:
    """
    returns driver names and their team names
    """
    fetch_data()
    current_year = get_present().year
    session_dates = get_future_sessions()
    #print(f"{current_year = }, {session_dates[0][0] = }")
    sess = fastf1.get_session(current_year,session_dates[0][0]-1,5)
    sess_loaded = sess.load()
    driver_names = [sess.get_driver(str(id))['BroadcastName'].split(" ",1)[1] for id in sess.drivers]
    driver_team = [sess.get_driver(str(id))['TeamName'] for id in sess.drivers]
    driver_details = list(zip(driver_names,driver_team))
    return driver_details


if __name__ == "__main__":
    print("\nLOCAL TEST:\n\n")
    res2 = get_last_session_results(1)
    print("\n",res2)