import sys
sys.path.append('.')
from include import core

def main():

    TOKEN = ""

    current_directory = core.os.getcwd()
    print(current_directory)

    if len(sys.argv) < 2:
        print("Usage: python3 module token")
        sys.exit(1)

    if len(sys.argv)==2:
        filename = sys.argv[1]
        try:
            with open(filename, "r") as f:
                TOKEN = f.read()
                print("Token found")
        except FileNotFoundError:
            print(f"Error: file '{filename}' not found.")
            sys.exit(1)

    core.logging_machine.createLog(str(core.datetime.datetime.now()), 
                                          'start-up', 
                                          core.inspect.currentframe().f_code.co_name,
                                          "server")

    core.bot.run(TOKEN)

    core.logging_machine.createLog(str(core.datetime.datetime.now()), 
                                          'shutdown', 
                                          core.inspect.currentframe().f_code.co_name,
                                          "server")

    print(f'Bot has been terminated')
    

main()
