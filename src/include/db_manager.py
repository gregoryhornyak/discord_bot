import json

DB_LOCATION = 'src/databases/'

def check_db_exists(db_name):
    db_name = DB_LOCATION+db_name
    db = {}
    try:
        with open(db_name,'r') as f:
            db = json.load(f)
    except FileExistsError:
        raise FileExistsError
    except FileNotFoundError:
        raise FileNotFoundError
    finally:
        if db:
            return True
        return False

def write_db(db_name): # fix json saving
    db = {'TIMESTAMP':{'event':'','user':'','guess':''}}
    db_name = DB_LOCATION+db_name
    with open(db_name,'w') as f:
        json.dump(db,f)
    pass

def read_db(db_name):
    db_name = DB_LOCATION+db_name
    with open(db_name,'r') as f:
        db = json.load(f)
    return db

def append_db(db_name,present,user,event,guess):
    print(f"appending started to {db_name} with {event} and {guess}")
    if not check_db_exists(db_name):
        write_db(db_name)
    db = read_db(db_name)
    db[present] = dict()
    db[present]['user'] = user
    db[present]['event'] = event
    db[present]['guess'] = guess
    db_name = DB_LOCATION+db_name 
    # this db_name directory path should be resolved, as rn it has to be inserted to each function
    # resolve directory path issue: for both databases and the modules
    with open(db_name,'w') as f: # should be 'a' as append
        json.dump(db,f)
    print(f"DB-MANAGER appended guess to {db_name}")
    """
    for k,v in db.items():
        print(k,v)
    """
    return 0

def last_entry(db_name,user,present):  # why 'present'?
    db = read_db(db_name)
    latest = '2023-01-01'
    for k,v in db.items():
        #print(k,v)
        if v['user'] == user:
            if k > latest:
                latest = k
    return latest, db[latest]


if __name__ == "__main__":
    append_db('db1.json','2023-02-12','GregHornyak','R','Hamilton')
    append_db('db1.json','2023-02-18','GregHornyak','Q','Perez')
    last_entry('db1.json','GregHornyak','2023-02-30')