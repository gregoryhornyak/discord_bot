# How To Setup the Project

> on Linux Ubuntu 22.04

<u>MUST HAVE</u>: **Python-3** and **GIT**

1. Download the repository with `git clone https://github.com/gregoryhornyak/discord_bot.git`
2. Install **virtualenv**: `sudo apt install virtualenv -y`
3. Setup the virtual environment: `virtualenv -p /usr/bin/python3 venv`
4. After setup, activate it: `source venv/bin/activate` <br> Then it should show `(venv)` in the left.
5. Now go to the main directory `discord_bot` and install the requirements: `pip install -r requirements.txt`
6. Then navigate to the `sample` directory and run the core app with `python3 sample/basic_bot.py src/token/token` <br> where the argument is the location of the token.

If you want to quit **venv**, type `deactivate`