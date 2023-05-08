import json

PATH = 'resources/data/'

def check_db_exists(db_name):
    """Check if a database exists with the same name"""
    db_name = PATH+db_name
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
    """Creates a database with an example content"""
    db = {'TIMESTAMP':{'event':'','user':'','guess':''}}
    db_name = PATH+db_name
    with open(db_name,'w') as f:
        json.dump(db,f)
    return 0

def read_db(db_name):
    """Reads the database from the file"""
    db_name = PATH+db_name
    with open(db_name,'r') as f:
        db = json.load(f)
    return db

# store event id
def append_db(db_name,present,user,event,guess):
    """appends the specified database with new content"""
    #print(f"appending started to {db_name} with {event} and {guess}")
    if not check_db_exists(db_name):
        write_db(db_name)
    db = read_db(db_name)
    db[present] = dict()
    db[present]['user'] = user
    db[present]['event'] = event
    db[present]['guess'] = guess
    db_name = PATH+db_name 
    # this db_name directory path should be resolved, as rn it has to be inserted to each function
    # resolve directory path issue: for both databases and the modules
    with open(db_name,'w') as f: # should be 'a' as append - not a because it reads and writes
        json.dump(db,f)
    #print(f"DB-MANAGER appended guess to {db_name}")
    return 0

def last_entry(db_name,user,present):  # why 'present'? to get the closest race 
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