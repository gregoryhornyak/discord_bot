# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands
import datetime
import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd

TOKEN_PATH = "resources/token/"
PASSW_PATH = "resources/passw"
UPLOADS_PATH = "resources/uploads/"
GUESS_FILE = "resources/guesses/"
SCORES_FILE = "resources/scores/"
LOGS_PATH = "resources/logs/"
VERSION = "0.1.2"

F1_RACES = ["FP1","FP2","FP3",
            "Q1st","Q2nd","Q3rd","Q-BOTR",
            "R1st","R2nd","R3rd","R-BOTR",
            "R-DOTD","R-F","R-DNF"]

# USE JSON AND DICTIONARIES
## OR
# PANDAS DATAFRAMES

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] - %(levelname)s : %(message)s') # maybe terminal doesnt need time and levelname

file_handler = logging.FileHandler(f"{LOGS_PATH}botlogs.md")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

current_directory = os.getcwd()
logger.info(f"{current_directory = }")

bot = commands.Bot(command_prefix='!',
                   intents=discord.Intents.all())

# event based functions

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}\n------\n')
    channel_id = bot.get_channel(1078427611597906004)
    boot_message = f"""
    Formula One Discord Bot v{VERSION}
is running in {channel_id.name} channel
Boot start: {datetime.datetime.now()}
"""
    await channel_id.send(boot_message)


@bot.command()#(aliases=["quit"])
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    await ctx.send("Bot will shutdown in 1sec")
    logger.debug("Bot Closed")
    await bot.close()

# every day: get the date, and check if its tomorrow or not
# - if tomorrow: print a message for everyone
# 

@bot.command()
async def upgrade(ctx,password):
    """reboots the whole bot, and updates it from Github"""
    password_stored = ""
    with open(f"{PASSW_PATH}",'r') as f:
        password_stored = f.read()
    if password!=password_stored:
        await ctx.send("Wrong password")
        return 0
    logger.info("BOT SHUTDOWN")
    await bot.close()

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

    async def race_callback(interaction):
        await interaction.response.send_message("a")

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
    #url = "https://ergast.com/api/f1/2023/14/drivers.json" # deprecated
    #url = "https://www.formula1.com/en/results.html/2023/races/1218/italy/race-result.html"
    drivers_url = "https://www.formula1.com/en/results.html/2023/drivers.html"
    drivers_request = requests.get(drivers_url).text
    logger.info("Successfully requested URL")
    drivers_soup = BeautifulSoup(drivers_request, 'html.parser')

    surnames = drivers_soup.find_all('span', class_="hide-for-mobile")
    firstnames = drivers_soup.find_all('span', class_="hide-for-tablet")
    carnames = drivers_soup.find_all('a', class_="grey semi-bold uppercase ArchiveLink")
    drivers_surnames = [name.get_text() for name in surnames]
    drivers_firstnames = [name.get_text() for name in firstnames]
    cars = [name.get_text() for name in carnames]
    drivers_fullname = list(zip(drivers_firstnames,drivers_surnames))
    drivers_info = list(zip(drivers_fullname,cars)) # (('Max', 'Verstappen'), 'Red Bull Racing Honda RBPT')
    select_race = discord.ui.Select(placeholder="Choose a race!",options=[discord.SelectOption(label=race_name, description="NONE") for race_name in F1_RACES])
    select_driver = discord.ui.Select(
        placeholder="Choose a driver",
        options=[
            discord.SelectOption(
                label=str(driver[0][0]+" "+driver[0][1]), 
                description=driver[1]
                ) 
                for driver in drivers_info]
                )
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
        logger.info(f"{ctx.author.name},{select_race.values[0]},{select_driver.values[0]}")
        await interaction.response.send_message("You have submitted your guess!")

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback
    await ctx.send("Choose driver and race type", view=theView)

# func to print user's current guess list 

# each race has their own id
#  <option value="1141/bahrain">Bahrain</option>

@bot.command()
async def evaluate(ctx):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    # get previous race id and name to request the race
    all_races_url = "https://www.formula1.com/en/results.html/2023/races.html"
    all_races_response = requests.get(all_races_url).text
    logger.info("Successfully requested URL")
    all_races_soup = BeautifulSoup(all_races_response, 'html.parser')
    
    race_names = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
    race_names_text = [name.get_text().strip() for name in race_names]
    logger.info(f"{race_names_text = }")

    race_ids = all_races_soup.find_all('a', class_='ArchiveLink')
    race_ids_text = [name.get('href') for name in race_ids]
    race_ids_text_splitted = [name.split('/')[5] for name in race_ids_text]
    logger.info(f"{race_ids_text_splitted = }")
    
    previous_race_id = race_ids_text_splitted[-1]
    previous_race_name = race_names_text[-1]

    # find out RACE results in previous race
    previous_race_url = f"https://www.formula1.com/en/results.html/2023/races/{previous_race_id}/{previous_race_name}/race-result.html"
    logger.info(f"{previous_race_url = }")
    previous_race_response = requests.get(previous_race_url).text
    driver_results_all_soup = BeautifulSoup(previous_race_response, 'html.parser')
    driver_results_all = driver_results_all_soup.find_all('tr')
    driver_results_all_text = [name.get_text().strip() for name in driver_results_all]
    driver_results_all_text_split = [name.split("\n") for name in driver_results_all_text]
    driver_results_all_filtered_list = [[item for item in original_list if item != ''] for original_list in driver_results_all_text_split]
    
    header_list = driver_results_all_filtered_list[0]
    driver_results_all_filtered_list = driver_results_all_filtered_list[1:]
    join_names = lambda arr: ' '.join(arr[2:4])
    dr_res_all_modified_data = [[*arr[:2], join_names(arr), *arr[5:]] for arr in driver_results_all_filtered_list]
    driver_results_all_df = pd.DataFrame(dr_res_all_modified_data, columns=header_list)
    logger.info(f"{driver_results_all_df = }")
    # headers: | Pos No Driver Car Laps Time/Retired PTS
    driver_results_all_df_message = driver_results_all_df.loc[:2, ['Driver', 'Time/Retired', 'PTS']]
    await ctx.send(driver_results_all_df_message.to_string(index=False, justify='left'))
    #logger.info(f"sent df {driver_results_all_df_message.to_string(index=False, justify='left') = }")

    # find out QUALIFYING results in previous race
    previous_race_q_url = f"https://www.formula1.com/en/results.html/2023/races/{previous_race_id}/{previous_race_name}/qualifying.html"
    previous_race_q_response = requests.get(previous_race_q_url).text
    driver_results_q_all_soup = BeautifulSoup(previous_race_q_response, 'html.parser')
    driver_results_q_all = driver_results_q_all_soup.find_all('tr')
    driver_results_q_all_text = [name.get_text().strip() for name in driver_results_q_all]
    driver_results_q_all_text_split = [name.split("\n") for name in driver_results_q_all_text]
    driver_results_q_all_filtered_list = [[item for item in original_list if item != ''] for original_list in driver_results_q_all_text_split]
    header_list = driver_results_q_all_filtered_list[0]
    driver_results_q_all_filtered_list = driver_results_q_all_filtered_list[1:]
    dr_res_q_all_modified_data = [[*arr[:2], join_names(arr), *arr[5:]] for arr in driver_results_q_all_filtered_list]
    driver_results_q_all_df = pd.DataFrame(dr_res_q_all_modified_data, columns=header_list)
    logger.info(f"{driver_results_q_all_df = }")
    
    def get_fpX_results(num):
    # find out FP1 results in previous race
        previous_race_fp1_url = f"https://www.formula1.com/en/results.html/2023/races/{previous_race_id}/{previous_race_name}/practice-{num}.html"
        previous_race_fp1_response = requests.get(previous_race_fp1_url).text
        driver_results_fp1_all_soup = BeautifulSoup(previous_race_fp1_response, 'html.parser')
        driver_results_fp1_all = driver_results_fp1_all_soup.find_all('tr')
        driver_results_fp1_all_text = [name.get_text().strip() for name in driver_results_fp1_all]
        driver_results_fp1_all_text_split = [name.split("\n") for name in driver_results_fp1_all_text]
        driver_results_fp1_all_filtered_list = [[item for item in original_list if item != ''] for original_list in driver_results_fp1_all_text_split]
        header_list = driver_results_fp1_all_filtered_list[0]
        driver_results_fp1_all_filtered_list = driver_results_fp1_all_filtered_list[1:]
        dr_res_fp1_all_modified_data = [[*arr[:2], join_names(arr), *arr[5:]] for arr in driver_results_fp1_all_filtered_list]
        driver_results_fp1_all_df = pd.DataFrame(dr_res_fp1_all_modified_data, columns=header_list)
        logger.info(f"FP{num} results: {driver_results_fp1_all_df = }")
        
    get_fpX_results(1)
    get_fpX_results(2)
    get_fpX_results(3)

    sprint_url = "https://www.formula1.com/en/results.html/2023/races/{race_id}/{race_name}/sprint-results.html"

    # send logs as pdf to report
        #cmd = f'pandoc {LOGS_PATH}botlogs.md -o {UPLOADS_PATH}bot_logs.pdf'
        #os.system(cmd)        
        #await ctx.send(file=discord.File(UPLOADS_PATH+"bot_logs.pdf"))

    return
    #get_previous_event_results = 

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

    present = f1_schedule.get_present()
    user = ctx.author.name
    date,latest = db_manager.last_entry(GUESS_FILE,user,present)
    await ctx.send(f"Your last guess was \n{latest['guess']} - {latest['event']} \nguessed on {date[:-10]}")
    
@bot.command()
async def nextdate(ctx):
    """show the next event's date"""
    await ctx.send('Lemme find it...')
    session_dates = f1_schedule.get_future_sessions()
    # display the serial number and the date
    await ctx.send(f'The next {session_dates[0][0]}. event is on {session_dates[0][1]}')
    logger.info("sent next_date")

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

    mid = "="
    mid += "="*int(length)
    if int(length) < 41:
        await ctx.send(f"itt egy meretes fasz csak neked:\n8{mid}D")
        logger.info("sent huge dong")
    else:
        await ctx.send(f'ekkora dakoval hogy tudsz te létezni?')
        logger.info("could not send huge dong")

@bot.command()
async def whoami(ctx):
    await ctx.send(f"You are {ctx.author.name}")
    await ctx.send(f"Hey <@{ctx.author.id}>")

@bot.command()
async def lajos(ctx, pia="palinka"):
    logger.info("lajos már régen volt az neten bazdmeg")
    script = """- Szia Lajos.
- Szia bazdmeg! Kutyáidat sétáltatod?
- Hát bazdmeg
- Ilyen...ilyen szerelésbe?
- Hát miér milyenbe?
- Miért nem öltözöl föl rendesen?
- Hát miér hát nem vagyok rendesen bazdmeg?
- Na jólvan.
- Most vettem fel bazdmeg délután!
- Ilyen... hát kár volt bazdmeg
- Hát ja
- Na jólvan szia
- Szia
...
Try '!lajos_mp3'"""
    if pia == "palinka":
        for line in script.split('\n'):
            await ctx.send(line)
    elif pia == "geci":
        await ctx.send("Húh, uauháuúháúáúháúu mi az apád faszát hoztál te buzi?")

@bot.command()
async def lajos_mp3(ctx):
    await ctx.send(file=discord.File(UPLOADS_PATH+"lajos_trim.mp3"))

@bot.command()
async def szeretsz_elni(ctx):

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

@bot.command()
async def hello(ctx):
    await ctx.send("Hello there")
    logger.info("hello func")

@bot.command()
async def kozso(ctx):
    await ctx.send("Az éérzéések, a szerelem, az ébredések, a kaják, a vizek, a min-mindent imádok!")
    logger.info("kozso func")
    
@bot.command()
async def predict(ctx):
    await ctx.send("Nem látok éppen semmit.")

@bot.command()
async def vitya(ctx):
    await ctx.send(file=discord.File(UPLOADS_PATH+"vitya.png"))

# Main function

if __name__ == "__main__":
    pass