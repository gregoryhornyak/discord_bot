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
UPLOADS_PATH = "resources/uploads/"
GUESS_FILE = "guesses.json"
RESULTS_FILE = "results.json"

F1_RACES = ["FP1","FP2","FP3","Q1st","Q2nd","Q3rd","Q-BOTR","R1st","R2nd","R3rd","R-BOTR","R-DOTD","R-F","R-DNF"]

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# event based functions

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------\n')

@bot.event
async def on_message_edit():
    print("A message has been changed\n------")

@bot.event
async def on_disconnect():
    print("Disconnected")

# command based functions

## essential

@bot.command()
async def admin_guess(ctx,password,date,guess,event):
    """allows the admin to make an artificial guess
    pw - date - guess - event
    date e.g.: 2023-05-08 15:11:26.272478
    """
    if password!="segg":
        await ctx.send("Wrong pass")
        return 0
    print(f"\n\n{date}\n{guess}\n{event}\n\n")
    regex_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+" # datetime regex
    print(f"{re.findall(regex_pattern, date) = }")
    if re.findall(regex_pattern, date)[0] != date:
        raise Exception
    db_manager.append_db(GUESS_FILE,date,ctx.author.name,event,guess)
    await ctx.send(f"Successfully saved:\n{date}\n{guess}\n{event}")

@bot.command()
async def admin_update(ctx):
    """allows the admin to update the database"""
    await ctx.send("Fetching has begun... may take a while")
    f1_drivers_info = f1_schedule.get_session_drivers()
    select_race = discord.ui.Select(placeholder="Choose a race type:",options=
        [discord.SelectOption(label=race_name) for race_name in F1_RACES])
    select_driver = discord.ui.Select(placeholder="Choose a driver who won on this race:",options=
        [discord.SelectOption(label=driver[0], description=driver[1]) for driver in f1_drivers_info])
    press_button = discord.ui.Button(label="SUBMIT",style=discord.ButtonStyle.primary)
    view = discord.ui.View()
    view.add_item(select_driver)
    view.add_item(select_race)
    view.add_item(press_button)

    async def driver_callback(interaction):
        await interaction.response.send_message("a")

        logging_machine.createLog(str(datetime.datetime.now()), 
                                          'choice', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"updated driver: {select_driver.values[0]}")
    async def race_callback(interaction):
        await interaction.response.send_message("a")
        logging_machine.createLog(str(datetime.datetime.now()), 
                                          'choice', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"updated race type: {select_race.values[0]}")
    async def button_callback(interaction):
        session_dates = f1_schedule.get_future_sessions()
        db_manager.store_results(RESULTS_FILE,2023,session_dates[0][0],select_race.values[0],select_driver.values[0])
        print("DB-MANAGER has appended the result")
        await interaction.response.send_message(f"You have updated:\nrace type: {select_race.values[0]}\nwinner driver: {select_driver.values[0]}\n")# print everything at once

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback

    await ctx.send("Choose driver who won and the race type they won in", view=view)

@bot.command()
async def guess(ctx):
    """Allows the user to make a guess"""
    await ctx.send("Fetching has begun... may take a while")
    f1_drivers_info = f1_schedule.get_session_drivers()
    f1_races = F1_RACES.copy()
    
    select_race = discord.ui.Select(placeholder="Choose a race!",options=[discord.SelectOption(label=race_name, description="NONE") for race_name in f1_races])
    select_driver = discord.ui.Select(placeholder="Choose a driver",options=[discord.SelectOption(label=driver[0], description=driver[1]) for driver in f1_drivers_info])
    press_button = discord.ui.Button(label="SUBMIT",style=discord.ButtonStyle.primary)
    
    theView = discord.ui.View()
    theView.add_item(select_race)
    theView.add_item(select_driver)
    theView.add_item(press_button)
    
    async def driver_callback(interaction):
        await interaction.response.send_message("")

    async def race_callback(interaction):
        await interaction.response.send_message("")

    async def button_callback(interaction):
        db_manager.append_db(GUESS_FILE,f1_schedule.get_present(),ctx.author.name,f1_schedule.get_future_sessions()[0][0],select_race.values[0],select_driver.values[0])
        print("DB-MANAGER appended guess")
        await interaction.response.send_message("You have submitted your guess!")# todo: print everything at once

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback
    await ctx.send("Choose driver and race type", view=theView)
    """
    guesses could be stored 
    """

@bot.command()
async def evaluate(ctx):
    """read the results, and compare them with the guesses"""
    # collect every result for the current event
    current_event_id = f1_schedule.get_future_sessions()[0][0]
    results = db_manager.read_db(RESULTS_FILE)
    winners = []

    for id,values in results.items():
        for race in F1_RACES:
            if values["event_id"] == current_event_id: # event found
                if values["race"] == race:
                    winners.append([race,values["driver"]])
                    

    # collect every user and their guesses for this event sorted by date
    # compare result and user guess, create a new db on points for each user
    # say hint to get results
    await ctx.send("jelenleg a joanyad fog kiértékelni, amikor nincs mibű")

@bot.command()
async def showlast(ctx):
    """show your last guess"""
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"last entry request")
    present = f1_schedule.get_present()
    user = ctx.author.name
    date,latest = db_manager.last_entry(GUESS_FILE,user,present)
    await ctx.send(f"Your last guess was \n{latest['guess']} - {latest['event']} \nguessed on {date[:-10]}")
    

@bot.command()
async def nextdate(ctx):
    """show the next event's date"""
    logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"next event request")
    await ctx.send('Lemme find it...')
    session_dates = f1_schedule.get_future_sessions()
    # display the serial number and the date
    await ctx.send(f'The next {session_dates[0][0]}. event is on {session_dates[0][1]}')

@bot.command()
async def last_results(ctx,prev=0):
    """show the results of the last session"""
    await ctx.send("Please wait, may take a while...")
    results, last_id, last_date = f1_schedule.get_last_session_results(back=prev)
    #print(f'{last_date.strftime("%Y-%m-%d") = }')
    db_manager.create_md_and_print(results.iloc[:,[1,8,13,14,15]].to_markdown(),str(last_id),str(last_date.strftime("%Y-%m-%d")))
    print(results.to_string(index=False))
    cmd = f'pandoc {UPLOADS_PATH}../data/last_session_results.md -o {UPLOADS_PATH}last_results_board.pdf'
    os.system(cmd)
    # pdfcrop --margins '30 20 30 -450' last_results_board.pdf last_board_crop.pdf
    cmd2 = f'pdftoppm {UPLOADS_PATH}last_results_board.pdf {UPLOADS_PATH}pretty_board -png -H 700'
    os.system(cmd2)
    await ctx.send(file=discord.File(UPLOADS_PATH+"pretty_board-1.png"))
    #await ctx.send(results.iloc[:,[1,8,15]].to_string(index=False))


## For fun

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

# Main function

if __name__ == "__main__":
    pass