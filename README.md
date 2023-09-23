# Formula One Discord Bot

![mylogo](docs/images/f1_disc_logo-removebg-preview.png)

#### Automated bot for a Discord server to fetch Formula One results

![Version](https://img.shields.io/badge/version-0.4.8-green) ![Deps](https://img.shields.io/badge/dependencies-up_to_date-green) ![Python](https://img.shields.io/badge/python-3.10-yellow) ![build](https://img.shields.io/badge/build-passing-yellow) ![build](https://img.shields.io/badge/progress-69-yellow)

---

## Functionality

### Guess

![screenshot from Discord](docs/images/guess_recording.gif)

![screenshot from Discord](docs/images/dnf_recording.gif)

### See your guesses

![screenshot from Discord](docs/images/myguess_recording.gif)

### Evaluate your guesses based on the latest results

---

## Key Features

- Access to official results ✅
- Running continuously (on AWS) ✅
- User can make guesses on a driver or dnf for each event ✅
- User can retrieve their guesses in form of a picture ✅
- Evaluate user guesses based on results ✅
- Inform clients on upcoming event date 🕐
- Working parallelly, having multiple clients ✅

---

## Content of repository

- [Commands](docs/commands.md)
- [Categories](docs/categories.md)

---

### Use case

1. User makes a guess from the possible options.
2. The system saves the guess until the corresponding event occurs.
3. After the event, the system fetches the results and runs a comparison between the guesses and the results.
4. The system evaluates the results and creates a score board for each player. 

---

## Contributors

J. Gergely Hornyak as **developer**

Gabor Korecz with **technical support** and **testing**

Marton Banfi as **tester**
