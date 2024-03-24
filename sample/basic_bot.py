import sys
sys.path.append('.')
from include import core

def main():

    TOKEN = ""

    if len(sys.argv) < 2:
        core.logger.error("Usage: python3 module token")
        sys.exit(1)

    if len(sys.argv)==2:
        filename = sys.argv[1]
        try:
            with open(filename, "r") as f:
                TOKEN = f.read()
                core.logger.info("Token found")
        except FileNotFoundError:
            core.logger.error(f"Error: file '{filename}' not found.")
            sys.exit(1)

    core.bot.run(TOKEN)

    core.logger.info(f'Bot has been terminated')

if __name__ == "__main__":
    main()
