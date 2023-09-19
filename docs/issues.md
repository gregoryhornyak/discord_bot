1. path errors: ../src/ and etc <br> should be globalised: every function uses the same path given in the basic_bot.py
2. needed a core.py, and the basic_bot.py would use the core.py to create a bot object
3. Ergast gave up
4. FastF1 is a bunch of crap

todo:

- the bot should run automates tests every first bootup of the day:
  - check databases, requests, connection, modules, dependencies

- maybe move to YAML files

- use a daily database fetches every morning
  - so no need for fetching time, quick access, local data

- alarm should a activate:
  - morning fetching,
  - race within time boundary (eg. 3 days)

add new Updates Page for any upcoming update