import os

def get_file_path():

    log_directory_path = '../src/databases'

    if not os.path.exists(log_directory_path):
        os.makedirs(log_directory_path)

    file_path = os.path.join(log_directory_path, 'system_log.txt')

    return file_path


def createLog(timestamp, direction, function_name, user, **data) -> str:
    """
    timestamp: when did it start
    direction: input or output
    function_name: which function was utilised
    user: who was the client
    """
    message = ""
    message += f"\nTIMESTAMP: {timestamp}"
    message += f"\nDIRECTION: {direction}"
    message += f"\nFUNCTION_NAME: {function_name}"
    message += f"\nUSER: {user}"
    try:
        if data["data"]:
            user_data = data["data"]
            message += f"\nDATA: {user_data}"
    except: pass
    message += "\n>-----<"
    writeLog(message)

def writeLog(message) -> None:
    with open(get_file_path(),"a") as logs: # issue with file generation upon first time (when it doesnt exist)
        logs.writelines(message)

    