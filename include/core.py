# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands, tasks
import datetime
import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json

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


@bot.command(name='guess', brief='guess driver and race_type')
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
        data = {
            "user_name": ctx.author.name,
            "race_type": select_race.values[0],
            "driver_name": select_driver.values[0]
            }
        
        try:
            with open(f"{GUESS_FILE}guess_db.json", "r") as f:
                guesses_database = json.load(f)
        except FileNotFoundError:
            guesses_database = {}
            logger.error("No guess_db found")

        present = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")
        guesses_database[present] = data
        logger.info("Guess_db updated")

        with open(f"{GUESS_FILE}guess_db.json", "w") as f:
                json.dump(guesses_database, f, indent=4)

        logger.info("Guess saved")

        await interaction.response.send_message("You have submitted your guess!")

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback
    await ctx.send("Choose driver and race type\n**(use this form for multiple guesses)**", view=theView)

# func to print user's current guess list 

# each race has their own id
#  <option value="1141/bahrain">Bahrain</option>

@bot.command()
async def eval(ctx):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    # headers: | Pos No Driver Car Laps Time/Retired PTS

    # get previous race id and name to request the race
    all_races_url = "https://www.formula1.com/en/results.html/2023/races.html"
    all_races_response = requests.get(all_races_url).text
    #logger.info("Successfully requested URL")
    all_races_soup = BeautifulSoup(all_races_response, 'html.parser')
    
    race_names = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
    race_names_text = [name.get_text().strip() for name in race_names]
    #logger.info(f"{race_names_text = }")

    race_ids = all_races_soup.find_all('a', class_='ArchiveLink')
    race_ids_text = [name.get('href') for name in race_ids]
    race_ids_text_splitted = [name.split('/')[5] for name in race_ids_text]
    #logger.info(f"{race_ids_text_splitted = }")
    
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
    #logger.info(f"{driver_results_all_df = }")
    
    r1st = driver_results_all_df.loc[0]['Driver']
    r2nd = driver_results_all_df.loc[1]['Driver']
    r3rd = driver_results_all_df.loc[2]['Driver']
    
    r_botr = ""

    for (driver, team) in (zip(driver_results_all_df['Driver'], driver_results_all_df['Car'])):
        if team not in ['Ferrari','Red Bull Racing Honda RBPT','Mercedes']:
            r_botr = driver
            logger.info(f"{r_botr = }")
            break

    r_dnf = 0

    for state in driver_results_all_df['Time/Retired']:
        if state in ['DNS','DNF']:
            r_dnf += 1



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
    #logger.info(f"{driver_results_q_all_df = }")

    q1st = driver_results_q_all_df.loc[0]['Driver']
    q2nd = driver_results_q_all_df.loc[1]['Driver']
    q3rd = driver_results_q_all_df.loc[2]['Driver']
    
    q_botr = ""

    #logger.info(f"{driver_results_q_all_df.loc[:, ['Driver','Car']] = }")
    

    # not Ferrari, Red Bull or Mercedes
    #for [driver,team] in driver_results_q_all_df.loc[:, ['Driver','Car']]:
    for (driver, team) in (zip(driver_results_q_all_df['Driver'], driver_results_q_all_df['Car'])):
        if team not in ['Ferrari','Red Bull Racing Honda RBPT','Mercedes']:
            q_botr = driver
            logger.info(f"{q_botr = }")
            break

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
        #logger.info(f"FP{num} results: {driver_results_fp1_all_df = }")
        return driver_results_fp1_all_df.loc[0]['Driver']
        
    fp1_results = get_fpX_results(1)
    fp2_results = get_fpX_results(2)
    fp3_results = get_fpX_results(3)

    # https://www.formula1.com/en/results.html/2023/races/1216/belgium/race-result.html
    # find sprint results
    sprint_race_id = "1216"
    sprint_race_name = "belgium"
    sprint_url = f"https://www.formula1.com/en/results.html/2023/races/{sprint_race_id}/{sprint_race_name}/sprint-results.html"
    previous_race_s_response = requests.get(sprint_url).text
    driver_results_s_all_soup = BeautifulSoup(previous_race_s_response, 'html.parser')
    driver_results_s_all = driver_results_s_all_soup.find_all('tr')
    driver_results_s_all_text = [name.get_text().strip() for name in driver_results_s_all]
    driver_results_s_all_text_split = [name.split("\n") for name in driver_results_s_all_text]
    driver_results_s_all_filtered_list = [[item for item in original_list if item != ''] for original_list in driver_results_s_all_text_split]
    header_list = driver_results_s_all_filtered_list[0]
    join_names = lambda arr: ' '.join(arr[2:4])
    driver_results_s_all_filtered_list = driver_results_s_all_filtered_list[1:]
    dr_res_s_all_modified_data = [[*arr[:2], join_names(arr), *arr[5:]] for arr in driver_results_s_all_filtered_list]
    driver_results_s_all_df = pd.DataFrame(dr_res_s_all_modified_data, columns=header_list)
    #logger.info(f"{driver_results_s_all_df = }")

    # driver of the day
    dotd_url = "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html"
    previous_race_dotd_response = requests.get(dotd_url).text
    previous_race_dotd_soup = BeautifulSoup(previous_race_dotd_response, 'html.parser')
    previous_race_dotd_all = previous_race_dotd_soup.find_all('strong')
    previous_race_dotd_all_text = [name.get_text().strip() for name in previous_race_dotd_all]
    dotd_list = previous_race_dotd_all_text[1]#latest
    # 'Carlos Sainz - 31.5%\nSergio Perez - 14.8%\nMax Verstappen - 13.3%\nAlex Albon - 10.7%\nCharles Leclerc - 6%',
    dotd = dotd_list.split("\n")[0]
    dotd_name = dotd.split("-")[0].strip()
    #logger.info(f"{dotd_name =}")

    rf_url = "https://www.formula1.com/en/results.html/2023/fastest-laps.html"
    race_fastest_lap_request = requests.get(rf_url).text
    race_fastest_lap_soap = BeautifulSoup(race_fastest_lap_request, 'html.parser')
    race_fastest_lap_all = race_fastest_lap_soap.find_all('tr')
    race_fastest_lap_all_text = [name.get_text().strip() for name in race_fastest_lap_all]
    race_fastest_lap_all_text_split = [name.split("\n") for name in race_fastest_lap_all_text]
    race_fastest_lap_all_filtered = [[item for item in original_list if item != ''] for original_list in race_fastest_lap_all_text_split]
    header_list = race_fastest_lap_all_filtered[0]
    join_names = lambda arr: ' '.join(arr[1:3])
    race_fastest_lap_all_filtered = race_fastest_lap_all_filtered[1:]
    race_fastest_lap_all_modified = [[*arr[:1], join_names(arr), *arr[4:]] for arr in race_fastest_lap_all_filtered]
    race_fastest_lap_all_df = pd.DataFrame(race_fastest_lap_all_modified, columns=header_list)
    #logger.info(f"{race_fastest_lap_all_df.iloc = }")

    r_f = race_fastest_lap_all_df.iloc[-1]['Driver']
    """
    logger.info(f"FP1: {fp1_results}")
    logger.info(f"FP2: {fp2_results}")
    logger.info(f"FP3: {fp3_results}")

    logger.info(f"Q1st: {q1st}")
    logger.info(f"Q2nd: {q2nd}")
    logger.info(f"Q3rd: {q3rd}")
    logger.info(f"Q-BOTR: {q_botr}")

    logger.info(f"R1st: {r1st}")
    logger.info(f"R2nd: {r2nd}")
    logger.info(f"R3rd: {r3rd}")
    logger.info(f"R-BOTR: {r_botr}")

    logger.info(f"DOTD: {dotd_name}")
    logger.info(f"R-F: {r_f}")
    logger.info(f"R-DNF: {r_dnf}")
    """
    scores = f"""
FP1: {fp1_results}
FP2: {fp2_results}
FP3: {fp3_results}
Q1st: {q1st}
Q2nd: {q2nd}
Q3rd: {q3rd}
Q-BOTR: {q_botr}
R1st: {r1st}
R2nd: {r2nd}
R3rd: {r3rd}
R-BOTR: {r_botr}
DOTD: {dotd_name}
R-F: {r_f}
R-DNF: {r_dnf}
    """




    #await ctx.send(scores)
    await ctx.send("Faszt kapsz te, nem kiértékelést")
    await ctx.send("Najó, kiértékelést akarsz?\szar vagy. meg buzi :D")
    #await ctx.send(file=discord.File(UPLOADS_PATH+"verstappen.mp3"))

    scores_json = {
    "FP1": fp1_results,
    "FP2": fp2_results,
    "FP3": fp3_results,
    "Q1st": q1st,
    "Q2nd": q2nd,
    "Q3rd": q3rd,
    "Q-BOTR": q_botr,
    "R1st": r1st,
    "R2nd": r2nd,
    "R3rd": r3rd,
    "R-BOTR": r_botr,
    "DOTD": dotd_name,
    "R-F": r_f,
    "R-DNF": r_dnf,
    }

    # evaluating method / system:
    # 1. find all the users who guessed (if didnt, out of game)
    # 2. if more guesses under same race_type then latest matters.
    # 3. if didnt guess in a race_type then doesnt get points

    # collect users

    #user_guesses = pd.read_json(f"{GUESS_FILE}guess_db.json")
    with open(f"{GUESS_FILE}guess_db.json", "r") as f:
                guesses_database = json.load(f)
    user_guesses = pd.DataFrame.from_dict(guesses_database, orient='index')
    user_guesses.reset_index(inplace=True)
    user_guesses.rename(columns={'index': 'time_stamp'}, inplace=True)
    user_guesses_reversed = user_guesses.iloc[::-1]
    logger.info(f"{user_guesses_reversed = }")
    # appropriate table ready

    users_in_game = user_guesses['user_name'].unique()

    for user in users_in_game:

        cur_user = user_guesses_reversed[user_guesses_reversed['user_name'] == user]
        #logger.info(f"{cur_user = }")
        #logger.info(f"{cur_user.drop_duplicates(subset=['race_type']) = }")
        cur_user_unique = cur_user.drop_duplicates(subset=['race_type'])

        for (guessed_race_type, guessed_driver_name) in (zip(cur_user_unique['race_type'], cur_user_unique['driver_name'])):
            for race_type,driver_name in scores_json.items():
                if guessed_race_type == race_type:
                    if guessed_driver_name == driver_name:
                        logger.info(f"{user}: match! {driver_name},{race_type}")
                        await ctx.send(f"{user} guessed correct: {driver_name} | {race_type} - X points!")



@bot.command()
async def rules(ctx):
    rule_book = """
Rules for guessing:
1. find all the users who guessed (if didnt, out of game)
2. if more guesses under same race_type then latest matters.
3. if didnt guess in a race_type then doesnt get points
"""
    await ctx.send(rule_book)

@bot.command()
async def getlogs(ctx):
    """ send logs as pdf to report"""
    cmd = f'pandoc {LOGS_PATH}botlogs.md -o {UPLOADS_PATH}bot_logs.pdf'
    os.system(cmd)        
    await ctx.send(file=discord.File(UPLOADS_PATH+"bot_logs.pdf"))

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
async def play_music(ctx):
    await ctx.connect()
    server = ctx.message.guild
    voice_channel = server.voice_client
    async with ctx.typing():
        player = await YTDLSource.from_url(playlist[0], loop=client.loop)
        voice_channel.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(after_play(ctx), client.loop))
        print(player.title)
    await ctx.send('**Now playing:** {}'.format(player.title))

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