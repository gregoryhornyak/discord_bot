# This example requires the 'members' and 'message_content' privileged intents to function, therefore using intents=discord.Intents.all()

#----< Imports >----#

import discord
from discord.ext import commands, tasks
import datetime
import os
import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import asyncio
from dateutil.parser import parse

#----< Constants >----#

UPCOMING_DATE_PATH = "resources/data/"
SCORE_TABLE_PATH = "resources/data/"
TOKEN_PATH = "resources/token/"
PASSW_PATH = "resources/passw/"
UPLOADS_PATH = "resources/uploads/"
GUESS_FILE = UPCOMING_DATE_PATH
SCORES_FILE = "resources/scores/"
LOGS_PATH = "resources/logs/"
MANIFEST_PATH = "docs/manifest/"
SCORE_TABLE_PUBLIC_PATH = "docs/"


F1_RACES = ["FP1","FP2","FP3",
            "Q1st","Q2nd","Q3rd","Q-BOTR",
            "R1st","R2nd","R3rd","R-BOTR",
            "R-DOTD","R-F","R-DNF"]

CHANNEL_ID = 1078427611597906004

# USE JSON
## AND
# PANDAS DATAFRAMES

#----< Logger init >----#

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] - %(levelname)s : %(message)s') # maybe terminal doesnt need time and levelname

file_handler = logging.FileHandler(f"{LOGS_PATH}botlogs.md")
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s : %(message)s')
file_handler.setFormatter(formatter)

logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

#----< Working directory >----#

current_directory = os.getcwd()
logger.info(f"{current_directory = }")

#----< Bot init >----#

bot = commands.Bot(command_prefix='!',
                   intents=discord.Intents.all())

#----< FUNCTIONS >----#

#--------< Event Based Functions >----#

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}\n------\n')
    channel_id = bot.get_channel(CHANNEL_ID)
    with open(f"{MANIFEST_PATH}manifest.json",'r') as f:
        manifest_info = json.load(f)
    boot_message = f"""
    {manifest_info['bot_name']} v{manifest_info['version']}
is running in {channel_id.name} channel
Boot start: {datetime.datetime.now()}
Created by {manifest_info['developer']}
"""
    await channel_id.send(boot_message,delete_after=5)

    # create resources directory and subdirectories
    try:
        directory = "resources"
        path = os.path.join('./', directory)
        os.mkdir(path)
        print("Directory '% s' created" % directory)
    except FileExistsError:
        logger.info("Resources dir already exists")

    await schedule_daily_message()


async def schedule_daily_message():
    loop_counter = 0
    while True:
        channel = bot.get_channel(CHANNEL_ID)
        try:
            with open(f"{UPCOMING_DATE_PATH}upcoming_date", "r") as f:
                upcoming_date = f.readline()
                upcoming_date = parse(upcoming_date)
            logger.info(f"Date already set for: {upcoming_date}")
        except FileNotFoundError:
            logger.info("Not found")

        now = datetime.datetime.now()
        if now.day+1 >= upcoming_date.day:
            logger.info(f"date is tomorrow!")
            await channel.send("@everyone the race is due!",delete_after=3)
        elif now.day+3 >= upcoming_date.day:
            logger.info(f"3 days until race!")
            await channel.send("@everyone 3 days until the race!",delete_after=3)
        #then = now.replace(minute=21)
        #wait_time = (then-now).total_seconds()
        loop_counter += 1
        logger.info(f"{loop_counter = }")
        await asyncio.sleep(30)

#--------< Core Command Functions >----#

@bot.command()
async def upgrade(ctx,password):
    """reboots the whole bot, and updates it from Github"""
    password_stored = ""
    with open(f"{PASSW_PATH}passphrase",'r') as f:
        password_stored = f.read()
    if password!=password_stored:
        await ctx.send("Wrong password")
        return 0
    logger.info("BOT SHUTDOWN")
    await bot.close()

@bot.command(aliases=["g","makeguess"])
async def guess(ctx):
    """Allows the user to make a guess"""
    await ctx.send("Fetching has begun... may take a while")

    # save the data into a file, to avoid long fetching

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
    select_race = discord.ui.Select(placeholder="Choose a race!",
                                    options=[discord.SelectOption(label=race_name, description="NONE") for race_name in F1_RACES])
    select_driver = discord.ui.Select(placeholder="Choose a driver",
                                      options=[discord.SelectOption(label=str(driver[0][0]+" "+driver[0][1]),
                                                                    description=driver[1]) for driver in drivers_info])
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

@bot.command(aliases=["e","evaluate"])
async def eval(ctx):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    # headers: | Pos No Driver Car Laps Time/Retired PTS
    await ctx.send("Fetching has begun... may take a while")

    class F1DataFetcher:
        # class variables:
        ## race details
        prev_race_id = 0
        prev_race_name = ""
        free_prac_ser_num = 1

        ## common lists
        best_three = ['Ferrari','Red Bull Racing Honda RBPT','Mercedes']

        ## urls
        all_races_url = "https://www.formula1.com/en/results.html/2023/races.html"
        prev_race_results_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/race-result.html"
        prev_qual_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/qualifying.html"
        prev_free_prac_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/practice-{free_prac_ser_num}.html"
        prev_sprint_url = f"https://www.formula1.com/en/results.html/2023/races/{prev_race_id}/{prev_race_name}/sprint-results.html"
        prev_dotd_url = "https://www.formula1.com/en/latest/article.driver-of-the-day-2023.5wGE2ke3SFqQwabYVQXLnF.html"
        prev_rf_url = "https://www.formula1.com/en/results.html/2023/fastest-laps.html"

        ## race types and scores

        fp1,fp2,fp3,q1st,q2nd,q3rd,q_botr,r1st,r2nd,r3rd,r_botr,dotd,r_fast,r_dnf = [0] * 14

        scores_json = {
            "FP1": fp1,
            "FP2": fp2,
            "FP3": fp3,
            "Q1st": q1st,
            "Q2nd": q2nd,
            "Q3rd": q3rd,
            "Q-BOTR": q_botr,
            "R1st": r1st,
            "R2nd": r2nd,
            "R3rd": r3rd,
            "R-BOTR": r_botr,
            "DOTD": r_botr,
            "R-F": r_fast,
            "R-DNF": r_dnf
            }

        def __init__(self):
            pass

        def _request_and_get_soap(self,url) -> BeautifulSoup:
            response = requests.get(url).text
            soap = BeautifulSoup(response, 'html.parser')
            return soap

        def _join_names(self,start=2,end=4):
            return lambda arr: ' '.join(arr[start:end])

        def get_prev_race_id_and_name(self) -> None:
            """updates local-class id and name"""
            all_races_response = requests.get(self.all_races_url).text # ---------NEW FUNCTION
            all_races_soup = BeautifulSoup(all_races_response, 'html.parser') # --  SECTION
            all_races_names_data = all_races_soup.find_all('a', class_="dark bold ArchiveLink")
            all_races_names = [name.get_text().strip() for name in all_races_names_data]
            all_races_ids_data = all_races_soup.find_all('a', class_='ArchiveLink')
            all_races_ids = [name.get('href') for name in all_races_ids_data]
            all_races_ids_text = [name.split('/')[5] for name in all_races_ids]
            previous_race_id = all_races_ids_text[-1]
            previous_race_name = all_races_names[-1]
            logger.info(f"{previous_race_id = }\n{previous_race_name = }")
            F1DataFetcher.prev_race_id = previous_race_id
            F1DataFetcher.prev_race_name = previous_race_name

        def get_prev_race_results(self) -> None:
            """ r1-3, r-botr, r-dnf results """
            prev_race_response = requests.get(self.prev_race_results_url).text # ---NEW FUNCTION
            prev_race_soap = BeautifulSoup(prev_race_response, 'html.parser') # ----  SECTION
            """
            columns = ['Race', 'Date', 'Driver', 'Team', 'Laps', 'Time']
            data = []
            rows = prev_race_soap.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'a', 'span'])
                if cols:
                    cols = [col.get_text(strip=True) for col in cols]
                    cols = list(filter(None, cols))
                    data.append(cols)
            df = pd.DataFrame(data, columns=columns)
            df = df.transpose()     
            df['Date'] = pd.to_datetime(df['Date'], format='%d %b %Y')
            df['Laps'] = pd.to_numeric(df['Laps'], errors='coerce')
            logger.info(f"prev_race_table: {df}")
            """
            prev_race_table = prev_race_soap.find_all('tr')
            prev_race_table_text = [name.get_text().strip() for name in prev_race_table]
            logger.info(f"{prev_race_table_text = }")
            prev_race_table_text_clear = [name.split("\n") for name in prev_race_table_text]
            logger.info(f"{prev_race_table_text_clear = }")
            prev_race_table_filtered = [[item for item in original_list if item.strip() != ''] for original_list in prev_race_table_text_clear]
            logger.info(f"{prev_race_table_filtered = }")
            
            prev_race_table_header = prev_race_table_filtered[0]
            prev_race_table_filtered_values = prev_race_table_filtered[1:]
            join_names = self._join_names()
            prev_race_table_clean = [[*arr[:2], join_names(arr), *arr[5:]] for arr in prev_race_table_filtered_values]
            logger.info(f"{prev_race_table_clean = }")
            logger.info(f"{prev_race_table_header = }")
            prev_race_table_df = pd.DataFrame(prev_race_table_clean, columns=prev_race_table_header)
            
            self.r1st = prev_race_table_df.loc[0]['Driver']
            self.r2nd = prev_race_table_df.loc[1]['Driver']
            self.r3rd = prev_race_table_df.loc[2]['Driver']

            for (driver, team) in (zip(prev_race_table_df['Driver'], prev_race_table_df['Car'])):
                if team not in self.best_three:
                    self.r_botr = driver
                    break

            for state in prev_race_table_df['Time/Retired']:
                if state in ['DNS','DNF']:
                    self.r_dnf += 1


    f1_data_fetcher = F1DataFetcher()
    f1_data_fetcher.get_prev_race_id_and_name()
    logger.info(f1_data_fetcher.prev_race_results_url)
    f1_data_fetcher.get_prev_race_results()
    logger.info(f"{f1_data_fetcher.r1st}")
    return 0

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

    await ctx.send(scores_json)

    # evaluating method / system:
    # 1. find all the users who guessed (if didnt, out of game)
    # 2. if more guesses under same race_type then latest matters.
    # 3. if didnt guess in a race_type then doesnt get points
    # 4. assign score board value

    # collect score board entries

    with open(f'{SCORE_TABLE_PATH}score_table.json', 'r') as file1:
        first_data = json.load(file1)

    # Open and read the second JSON file
    with open(f'{SCORE_TABLE_PUBLIC_PATH}score_table_public.json', 'r') as file2:
        compare_data = json.load(file2)

    # Update the values in the second dictionary
    for key, value in compare_data.items():
        first_data[key] = value
    score_board = first_data
    with open(f'{SCORE_TABLE_PATH}score_table.json', 'w') as file2:
        json.dump(first_data, file2, indent=4)

    #logger.info(f"SCORE_BOARD: {first_data}")

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
        cur_user_unique = cur_user.drop_duplicates(subset=['race_type'])
        for (guessed_race_type, guessed_driver_name) in (zip(cur_user_unique['race_type'], cur_user_unique['driver_name'])):
            for race_type,driver_name in scores_json.items():
                if guessed_race_type == race_type:
                    if guessed_driver_name == driver_name:
                        logger.info(f"{user}: match! {driver_name},{race_type}")
                        points = score_board[race_type]
                        await ctx.send(f"{user} guessed correct: {driver_name} | {race_type} - {points} points!")


# update_odds func()


@bot.command(aliases=["date,when,next"])
async def setdate(ctx, *, date_input):
    try:
        parsed_date = parse(date_input)
        if parsed_date:
            # set_date 2023 09 16
            await ctx.send(f"Race date set to: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Race date set to: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')}")
            with open(f"{UPCOMING_DATE_PATH}upcoming_date","w") as f:
                f.write(parsed_date.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            await ctx.send("Invalid date format. Please use a valid date format.")
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")

#--------< Additional Functions >----#

@bot.command()
async def tutorial(ctx):
    tutorial = """
Start with setting the race event date - !setdate
Then make guesses - !g(uess)
Then wait until the event
Finally evaluate the results - !e(val)

(And start the whole process again)
"""
    await ctx.send()

@bot.command()
async def spy(ctx):
    guilds = bot.guilds
    guild = str(guilds).split("=")[1].split()[0]
    guild = int(guild)
    #guild = bot.get_guild(1078427611597906001)
    logger.info(f"manual: {guild = }")

    if guild:
        for member in guild.members:
            logger.info(f"{member.name}: <@{member.discriminator}>")
            await ctx.send(f"{member.name}: <@{member.id}>")
    else:
        logger.info("Guild not found")


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
async def getlogs(ctx, num_of_lines=500):
    """ send logs as pdf to report"""
    logger.info(f"getlogs with {num_of_lines} lines")
    with open(f"{LOGS_PATH}botlogs.md", 'r') as file:
        lines = file.readlines()[-(num_of_lines):]
    logger.info(f"read lines")
    with open(f"{LOGS_PATH}botlogs_extract.md", 'w') as file:
        for line in lines:
            file.write(line)
    logger.info(f"botlogs_extract.md populated")
    cmd = f'pandoc {LOGS_PATH}botlogs_extract.md -o {UPLOADS_PATH}botlogs_extract.pdf'
    os.system(cmd)        
    await ctx.send(file=discord.File(UPLOADS_PATH+"botlogs_extract.pdf"))
    # only send back last N number of lines to reduce file size

@bot.command(aliases=['get_my_guesses','mylast'])
async def myguesses(ctx):
    with open(f"{GUESS_FILE}guess_db.json", "r") as f:
            guesses_database = json.load(f)
    user_guesses = pd.DataFrame.from_dict(guesses_database, orient='index')
    user_guesses.reset_index(inplace=True)
    user_guesses.rename(columns={'index': 'time_stamp'}, inplace=True)
    user_guesses_reversed = user_guesses.iloc[::-1]
    
    cur_user = user_guesses_reversed[user_guesses_reversed['user_name'] == ctx.author.name]

    cur_user_unique = cur_user.drop_duplicates(subset=['race_type'])
    cur_user_unique.set_index('race_type', inplace=True)
    cur_user_unique = cur_user_unique.sort_values(by='race_type')
    logger.info(cur_user_unique)
    with open(f"{UPLOADS_PATH}user_guesses_list.md",'w') as f:
        f.write(f"# {ctx.author.name}'s guess list \n")
        f.write(cur_user_unique['driver_name'].to_markdown())
    cmd = f'pandoc {UPLOADS_PATH}user_guesses_list.md -o {UPLOADS_PATH}user_guesses_list.pdf'
    cmd2 = f'pdftoppm {UPLOADS_PATH}user_guesses_list.pdf {UPLOADS_PATH}user_guesses_list -png'
    os.system(cmd)
    os.system(cmd2)
    await ctx.send(file=discord.File(f"{UPLOADS_PATH}user_guesses_list-1.png"))

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


#--------< Funny Functions >----#

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
    logger.info(f"{ctx.author.id = }")

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
            await ctx.send(line,delete_after=5)
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
    - Tehát akkor annyira nem szeretsz élni? :)"""
    for line in script.split('\n'):
        await ctx.send(line,delete_after=4)

@bot.command()
async def hello(ctx):
    await ctx.send("Hello there")
    logger.info("hello func")

@bot.command()
async def kozso(ctx):
    await ctx.send("Az éérzéések, a szerelem, az ébredések, a kaják, a vizek, a min-mindent imádok!",delete_after=4)
    logger.info("kozso func")
    
@bot.command()
async def predict(ctx):
    await ctx.send("Nem látok éppen semmit.")

@bot.command()
async def vitya(ctx):
    await ctx.send(file=discord.File(UPLOADS_PATH+"vitya.png"))

"""
Functions not in use:

@bot.command()#(aliases=["quit"])
@commands.has_permissions(administrator=True)
async def shutdown(ctx):
    await ctx.send("Bot will shutdown in 1sec")
    logger.debug("Bot Closed")
    await bot.close()


"""

#----< Main Function Init >----#


if __name__ == "__main__":
    pass