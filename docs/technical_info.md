# System info

This bot was designed on Linux, meaning the setup is optimised for Linux distros.

The repository uses **python venv**, which needs to be initialised beforehand, and the required packages installed inside.  

A brief tutorial on setup is available [here](docs/setup.md).

### Mayor Update 1

**Formula One Discord Bot** is moving away from FastF1 Python package:

- the module isn't working properly,
- custom json requests are easier to make using Ergast directly

In the future, the Formula One Discord Bot is going to use Ergast as main information source for Race, Qualification, Finishing Status and Race schedules

### Mayor Update 2

**Formula One Discord Bot** is not going to use Ergast as primary API, because Ergast API is going to be deprecated in 2024.

---

## Components

The product: a Discord chatbot, listening and writing on a Discord feed / channel.

The core app, hosting the necessary files for the chatbot. Also making connection between the database and the Discord channel.
In addition, responsible for making the json requests from Ergast.

The database manager, handling the storing and retrieving actions, when dealing with the database(s).

The request_manager, handling the requests to Formula One official website.

~~logging machine~~

~~FastF1, a F1-API - a python package - fetching the F1 race data.~~

Formula One website as source

Discord.py Python package as API module
