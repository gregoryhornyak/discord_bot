import fastf1
import datetime

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

    fastf1.Cache.enable_cache('.')
    current_year = int(str(datetime.datetime.today().year))
    session_dates = [fastf1.get_session(current_year, r, 'R').date for r in range(1,24)]
    #session = fastf1.get_session(current_year, 6, 'FP1')
    return session_dates


def get_future_sessions():
    """return every future session date"""
    future_dates = filter(match_dates,get_session_dates())
    future_dates = [f for f in future_dates]
    return future_dates





