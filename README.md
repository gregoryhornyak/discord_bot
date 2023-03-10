# Custom Formula One Discord Bot

Automated bot for a Discord server

## Pipeline

1. User guesses F1 result
2. Result is stored in database
3. After race/event, results and guesses are compared
4. Scores for each player are evaluated
5. Repeat

## Commands

```
SIGN+COMMAND -> ARGUMENTS:[OPT]
```

## Structure

- Scoreboard | DB1: name - point per event - total points seasonal
- Input logs | DB2: timestamp - author - event - guess

|Scoreboard|Input logs|
|-|-|
|name|timestamp|
|points/event|author|
|total points|event|
||guess|

[The layout](docs/layout.md)

## Github commands

```
git pull
git add FILE
git commit -m "MESSAGE"
git status
git push
```

## Contributors

J. Gergely Hornyak
Gabor Korecz **as revisioning**


---
