# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands
import random
import asyncio
import datetime
import sys
import inspect
from include import f1_schedule
from include import db_manager
from include import logging_machine
import os
import re

TOKEN_PATH = "../resources/token/"
UPLOADS_PATH = "../resources/uploads/"
GUESS_FILE = "guesses.json"


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# event based functions

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------')

@bot.event
async def on_message_edit():
    print("A message has been changed\n------")

@bot.event
async def on_disconnect():
    print("Disconnected")

# command based functions

## essential

@bot.command()
async def goodbye(ctx):
    await ctx.send("BOT SHUTDOWN")
    await bot.close()

@bot.command()
async def menu(ctx):
    pass

@bot.command()
async def admin_guess2(ctx,date,guess,event):
    print(f"\n\n{date}\n{guess}\n{event}\n\n")
    regex_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+" # datetime regex
    print(f"{re.findall(regex_pattern, date) = }")
    if re.findall(regex_pattern, date)[0] != date:
        raise Exception
    db_manager.append_db(GUESS_FILE,date,ctx.author.name,event,guess)
    await ctx.send(f"Successfully saved:\n{date}\n{guess}\n{event}")

@bot.command()
async def guess2(ctx):
    await ctx.send("Fetching has begun... may take a while")
    f1_drivers, f1_teams = f1_schedule.get_session_drivers()
    f1_drivers_info = list(zip(f1_drivers,f1_teams))
    f1_races = ["FP1","FP2","FP3","Q-1st","Q-2nd","Q-3rd","Q-BEST","Sprint","R-1st","R-2nd","R-3rd","R-BEST","R-DOD","R-Fast","R-DNF"]

    select_driver = discord.ui.Select(placeholder="Choose a driver",options=
        [discord.SelectOption(label=driver[0], description=driver[1]) for driver in f1_drivers_info])
    select_race = discord.ui.Select(placeholder="Choose a race!",options=
        [discord.SelectOption(label=race_name, description="ADD DESCRIPTION") for race_name in f1_races])
    press_button = discord.ui.Button(label="SUBMIT",style=discord.ButtonStyle.primary)
    view = discord.ui.View()
    view.add_item(select_driver)
    view.add_item(select_race)
    view.add_item(press_button)

    async def driver_callback(interaction):
        await interaction.response.send_message(f"You have chosen {select_driver.values[0]}.")
        logging_machine.createLog(str(datetime.datetime.now()), 
                                          'choice', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"guessed driver: {select_driver.values[0]}")
    async def race_callback(interaction):
        await interaction.response.send_message(f"You have chosen {select_race.values[0]}.")
        logging_machine.createLog(str(datetime.datetime.now()), 
                                          'choice', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"guessed race type: {select_race.values[0]}")
    async def button_callback(interaction):
        db_manager.append_db(GUESS_FILE,f1_schedule.get_present(as_str=True),ctx.author.name,select_race.values[0],select_driver.values[0])
        print("DB-MANAGER appended guess")
        await interaction.response.send_message("You have submitted your guess!")
    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback
    await ctx.send("Choose driver and race type", view=view)
    """
    guesses could be stored 
    """

@bot.command()
async def guess(ctx,event,guess):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'input', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"event: {event}\n\tguess: {guess}")
    # prepare arguments
    present = f1_schedule.get_present(as_str=True)
    user = ctx.author.name
    # store input
    db_manager.append_db(GUESS_FILE,present,user,event,guess)
    # reply
    await ctx.send(f'Your guess {guess} for {event} has been saved.')

@bot.command()
async def showlast(ctx):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"last entry request")
    present = f1_schedule.get_present(as_str=True)
    user = ctx.author.name
    date,latest = db_manager.last_entry(GUESS_FILE,user,present)
    await ctx.send(f"Your last guess was \n{latest['guess']} - {latest['event']} \nguessed on {date[:-10]}")
    

@bot.command()
async def next(ctx):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"next event request")
    await ctx.send('Lemme find it...')
    session_dates = f1_schedule.get_future_sessions()
    await ctx.send(f'The next event is on {session_dates[0]}')

## For fun

@bot.command()
async def add(ctx, left: int, right: int):
    """Adds two numbers together."""
    await ctx.send(left + right)


@bot.command()
async def roll(ctx, dice: str):
    """Rolls a dice in NdN format."""
    try:
        rolls, limit = map(int, dice.split('d'))
    except Exception:
        await ctx.send('Format has to be in NdN!')
        return

    result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
    await ctx.send(result)


@bot.command(description='For when you wanna settle the score some other way')
async def choose(ctx, *choices: str):
    """Chooses between multiple choices."""
    await ctx.send(random.choice(choices))

@bot.command()
async def xbox(ctx):
    print("image requested")
    await ctx.send(file=discord.File(UPLOADS_PATH+"xbox.jpeg"))
    print("image sent")


@bot.command()
async def note(ctx,*notes): # input should be wrapped with " " to store as single word/sentence
    print(f"notes: {notes}")


@bot.command()
async def dako(ctx, length):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"length: {length}")
    mid = "="
    mid += "="*int(length)
    if int(length) < 41:
        await ctx.send(f"itt egy meretes fasz csak neked:\n8{mid}D")
    else:
        await ctx.send(f'ekkora dakoval hogy tudsz te létezni?')

@bot.command()
async def whoami(ctx):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name)
    for i in range(1):
        await ctx.send(f"You are {ctx.author.name}")

@bot.command()
async def button(ctx):
    view = discord.ui.View()
    button = discord.ui.Button(label="Nuke Israel")
    view.add_item(button)
    await ctx.send(view=view)

@bot.command()
async def what(ctx):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name)
    await ctx.send("""To guess a score: SIGN+guess -> SCORE
To see every guess: SIGN+board
To only see your guesses: SIGN+myboard""")

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')

@bot.command()
async def lajos(ctx):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                        'output', 
                                        inspect.currentframe().f_code.co_name,
                                        ctx.author.name)
    script = """-Szia Lajos.
-Szia bazdmeg! Kutyáidat sétáltatod?
-Hát bazdmeg
-Ilyen...ilyen szerelésbe?
-Hát miér milyenbe?
-Miért nem öltözöl föl rendesen?
-Hát miér hát nem vagyok rendesen bazdmeg?
-Na jólvan.
-Most vettem fel bazdmeg délután!
-Ilyen... hát kár volt bazdmeg
-Hát ja
-Na jólvan szia
-Szia
...
Try '!lajos_mp3'"""
    for line in script.split('\n'):
        await ctx.send(line)

@bot.command()
async def lajos_mp3(ctx):
    await ctx.send(file=discord.File(UPLOADS_PATH+"lajos_trim.mp3"))

@bot.command()
async def szeretsz_elni(ctx):
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name)
    script = """- Az lenne a kérdés hogy szeretek-e élni?
    - Élni? A gyász! ... 
    meg a ... 
    hogyhijjáka a gyász ... 
    meg a szenvedés ...
    Az az életem. :|
    - Tehát akkor annyira nem szeretsz élni? :)
    """
    for line in script.split('\n'):
        await ctx.send(line)

@bot.group()
async def cool(ctx):
    """Says if a user is cool.

    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')


@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')

# Main function

if __name__ == "__main__":
    pass