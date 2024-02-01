# How To Setup the Project

>on Linux Ubuntu 22.04 (x86_64)

MUST HAVE: **Python-3** and **GIT**

otherwise `sudo apt install git; sudo apt install python3.10`

1. Download the repository with `git clone https://github.com/gregoryhornyak/discord_bot.git`
2. Go inside the repository: `cd discord_bot`
3. Install **virtualenv**: `sudo apt install virtualenv -y`
4. Setup the virtual environment: `virtualenv -p /usr/bin/python3 venv`
5. After setup, activate it: `source venv/bin/activate` <br> Then it should show `(venv)` in the left.
6. Install the requirements: `pip install -r requirements.txt`
7. Create directories for resources: `sh setup_environment.sh`
8. Then run the core app with `python3 sample/basic_bot.py resources/token/token`  where the argument is the location of the token.

If you want to quit **venv**, type `deactivate`