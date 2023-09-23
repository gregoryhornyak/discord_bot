# This example requires the 'members' and 'message_content' privileged intents to function, therefore using intents=discord.Intents.all()

#----< Imports >----#

import discord
from discord.ext import commands
#from discord import app_commands

import datetime
import os

import typing

from discord.interactions import Interaction
from discord import voice_client 

from include.logging_manager import logger
from include.constants import *
import include.f1_data_fetcher as f1_data
import include.database_manager as db_man

import asyncio
from dateutil.parser import parse

##
## TODO
## 
##  Implement Sprint results
##


#----< Working directory >----#

current_directory = os.getcwd()
logger.info(f"{current_directory = }")

#----< Bot init >----#

bot = commands.Bot(command_prefix="/",intents=discord.Intents.all())

f1_module = f1_data.F1DataFetcher()

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}\n------\n')
    bot.tree.copy_global_to(guild=discord.Object(id=1078427611597906001))
    await bot.tree.sync(guild=discord.Object(id=1078427611597906001))
    channel = bot.get_channel(CHANNEL_ID)
    history_gen = channel.history(limit=1)
    list_of_messages = []
    async for result in history_gen:
        message = await channel.fetch_message(result.id)
        list_of_messages.append(message)
    await channel.delete_messages(list_of_messages,reason="Remove update alert message")
    man_version = get_manifest_version_info()

    with open(f"{MANIFEST_PATH}manifest.json", "r") as f:
        manifest_info = json.load(f)

    boot_message = f"""
{manifest_info['bot_name']} v{manifest_info['version']}
Latest version: {man_version}
Latest update: {manifest_info['latest']}
Boot date: {datetime.datetime.now()}
"""
    await channel.send(boot_message,delete_after=10)

    await schedule_daily_message()


def init_stage(cur_dir):
    dirs = ["data","config","inventory","logs","password","uploads","token"]
  
    # Parent Directory path
    parent_dir = f"{cur_dir}/resources/"
    
    # Path
    for dir in dirs:
        path = os.path.join(parent_dir,dir)
        try:
            os.mkdir(path)
        except FileExistsError:
            logger.info(f"{dir} already exists")
        else:
            logger.info(f"Created: {dir} dir")

def get_manifest_version_info():
    git_link = "https://github.com/gregoryhornyak/discord_bot/blob/master/docs/manifest/manifest.json?raw=true"
    manifest = f1_data.requests.get(git_link).json()
    return manifest['version']


"""
@bot.tree.command(name="del_all",description="long")
async def delete_all(ctx:Interaction):
    await ctx.response.defer()
    channel = bot.get_channel(CHANNEL_ID)
    history_gen = channel.history(limit=50)
    list_of_messages = [result async for result in history_gen]
    await channel.delete_messages(list_of_messages,reason="Remove update alert message")
    await ctx.followup.send(f"Deleted 50 messages")
"""
    
async def schedule_daily_message():
    loop_counter = 0
    upcoming_date = ""
    while True:
        channel = bot.get_channel(CHANNEL_ID)
        try:
            with open(f"{UPCOMING_DATE_PATH}upcoming_date", "r") as f:
                upcoming_date = f.readline()
            upcoming_date = parse(upcoming_date)
            #logger.info(f"Date once set for: {upcoming_date}")
        except FileNotFoundError:
            logger.info("Not found")
            # do something

        now = datetime.datetime.now()
        # race alert
        #   less than a day
        """
        if now.day <= upcoming_date.day:
            logger.info(f"Past race date")
        if now.day+1 >= upcoming_date.day:
            logger.info(f"date is tomorrow!")
            await channel.send("@everyone the race is due!",delete_after=3)
        #   less than 3 days
        elif now.day+3 >= upcoming_date.day:
            logger.info(f"3 days until race!")
            await channel.send("@everyone 3 days until the race!",delete_after=3)
        """
        # morning schedule: auto-testing, fetching
        if now.hour == 9 and now.minute == 5: # 8:05
            await channel.send("Doing daily routine")
        if now.hour == 21 and now.minute == 45: 
            await channel.send("21:45")
        loop_counter += 1
        await asyncio.sleep(50)

@bot.tree.command(name="upgrade",description="long")
async def upgrade(interaction:Interaction,password:str):
    """reboots the whole bot, and updates it from Github"""
    password_stored = ""
    with open(f"{PASSW_PATH}passw",'r') as f:
        password_stored = f.read()
    if password!=password_stored:
        await interaction.response.send_message("Wrong password")
        return 0
    logger.info("BOT SHUTDOWN")
    await interaction.response.send_message("Bot is shutting down and will be upgraded...")
    await bot.close()

# function to get every racing date -> save to file -> update alert 

def get_discord_members(ctx:Interaction):
    user_info = {}
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            user_info[member.name] = member.id
    return user_info

@bot.tree.command(name="guess",description="-")
async def guess(ctx:discord.Interaction): # Q: making the dropdown box into a slash command is a good option?
    """Allows the user to make a guess"""
    await ctx.response.defer(ephemeral=True)
    channel = bot.get_channel(CHANNEL_ID)
    #await channel.send("Fetching has begun... may take a while",delete_after=1)

    # save the data into a file, to avoid long fetching
    drivers_info = f1_module.get_drivers_details()
    #prev_race_id = get_prev_race_id_and_name()['id']
    #prev_race_name = get_prev_race_id_and_name()['name']
    next_race_id = f1_module.get_next_race_id_and_name()['id']
    next_race_name = f1_module.get_next_race_id_and_name()['name']

    select_race = discord.ui.Select(placeholder="Choose a race!",
                                    options=[discord.SelectOption(
                                        label=race_name, description="---") for race_name in F1_RACE_TYPES if race_name!="R_DNF"])
    select_driver = discord.ui.Select(placeholder="Choose a driver",
                                    options=[discord.SelectOption(
                                        label=driver,description=team) for driver,team in drivers_info.items()])
    press_button = discord.ui.Button(label="SUBMIT",style=discord.ButtonStyle.primary)
    theView = discord.ui.View()
    theView.add_item(select_race)
    theView.add_item(select_driver)
    theView.add_item(press_button)
    
    async def driver_callback(sub_interaction:Interaction):
        await sub_interaction.response.defer()

    async def race_callback(sub_interaction:Interaction):
        await sub_interaction.response.defer()

    async def button_callback(sub_interaction:Interaction):
        name = sub_interaction.user.name
        id = sub_interaction.user.id
        db_man.save_guess(name=name,id=id,select_race=select_race,select_driver=select_driver,next_race_id=next_race_id) # dnf=False
        await sub_interaction.response.send_message("✅",delete_after=1.3)

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback

    message = f"Guess for {next_race_name} {datetime.datetime.now().year}\n*For Race DNF, call '/dnf'*\n**(use this form for multiple guesses)**"
    await ctx.followup.send(content=message, view=theView)

#schedule_2023 = "https://www.formula1.com/en/latest/article.formula-1-update-on-the-2023-calendar.4pTQzihtKTiegogmNX5XrP.html"

@bot.tree.command(name="dnf",description="guess num of dnf")
async def dnf(interaction: discord.Interaction, guess: int):
    next_race_id = f1_module.get_next_race_id_and_name()['id']
    db_man.save_guess(name=interaction.user.name,id=interaction.user.id,select_race="R_DNF",select_driver=guess,dnf=True,next_race_id=next_race_id)
    await interaction.response.send_message(f'You guessed {guess} number of DNF(s)', ephemeral=True)

@bot.tree.command(name="get_msg",description="get channel history")
async def get_msg(interaction: discord.Interaction, dist:int=5):
    # sent_msg = await ctx.send("test message")
    # await ctx.send(f"{sent_msg.id = }")
    # msg = await ctx.fetch_message(sent_msg.id)
    # await ctx.send(f"{msg = }")
    history_gen = interaction.channel.history(limit=dist)
    async for result in history_gen:
        message = await interaction.channel.fetch_message(result.id)

        await interaction.channel.send(f"{message.content = }")
        # logger.info(f"message: {result}")
    await interaction.response.send_message(f"Found all {dist} past messages")

@bot.tree.command(name="history",description="-")
async def history(interaction:Interaction, dist:int=5):
    # sent_msg = await interaction.response.send_message("test message")
    # await interaction.response.send_message(f"{sent_msg.id = }")
    # msg = await interaction.fetch_message(sent_msg.id)
    # await interaction.response.send_message(f"{msg = }")
    history_gen = interaction.history(limit=dist)
    async for ser_num,result in enumerate(history_gen):
        message = await interaction.fetch_message(result.id)
        await interaction.response.send_message(f"{ser_num+1}: {message.content}")
        logger.info(f"message: {result}")
    await interaction.response.send_message(f"Found all {dist} past message(s)")

async def calendar(interaction:Interaction):
    schedule_2023_unknown = "https://www.autosport.com/f1/schedule/2023/"
    calendar_response = db_man.requests.get(schedule_2023_unknown).text
    calendar_soap = db_man.BeautifulSoup(calendar_response, 'html.parser')
    #logger.info(f"{calendar_soap = }")
    calendar_table = calendar_soap.find_all("tbody", class_="ms-schedule-table__item ms-schedule-table--local")
    logger.info(f"{calendar_table}")
    calendar_table_text = [name.get_text().strip() for name in calendar_table]
    logger.info(f"{calendar_table_text = }")
    calendar_table_text_clean = [name.split("\n") for name in calendar_table_text]
    logger.info(f"{calendar_table_text_clean = }")

@bot.tree.command(name="eval",description="-")
async def eval(ctx:Interaction):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    # FETCHING

    # save dataframes into data/fetched_data every morning

    # headers: | Pos No Driver Car Laps Time/Retired PTS
    await ctx.response.defer()
    scores_json = f1_module.get_all_results()
    logger.info(f"scores_json: {scores_json}")
    #await interaction.response.send_message(scores_json,delete_after=3)

    #await interaction.response.send_message(file=discord.File(UPLOADS_PATH+"verstappen.mp3"))

    # EVALUATING

    # 1. find all the users who guessed (if didnt, out of game)
    # 2. if more guesses under same race_type then latest matters.
    # 3. if didnt guess in a race_type then doesnt get points
    # 4. assign score board value

    # files needed:
    # - guess_db
    # - results
    # - score_table
    # - users_db
    # - F1-data
    # - all users

    # guess_db - users' guesses on race results
    try:
        with open(f"{INVENTORY_PATH}guess_db.json", "r") as f:
            guess_db = json.load(f)
    except FileNotFoundError:
        ctx.channel.send("No guesses yet")
        return 0

    # does it need to be transformed into a dataframe?
    guess_db = f1_data.pd.DataFrame.from_dict(guess_db, orient='index')
    guess_db.reset_index(inplace=True)
    guess_db.rename(columns={'index': 'time_stamp'}, inplace=True)
    guess_db_reversed = guess_db.iloc[::-1]
    #logger.info(f"{guess_db_reversed = }")

    # f1 data

    race_id = f1_module.get_prev_race_id_and_name()['id']
    race_name = f1_module.get_prev_race_id_and_name()['name']

    # results - official results
    # existence assured by f1_module
    with open(f"{RESULTS_PATH}results.json", "r") as f:
        results = json.load(f)
    results = results[race_id]

    # collect score table entries
    try:
        with open(f'{SCORE_TABLE_PATH}score_table.json', 'r') as f:
            scoring_board = json.load(f)
    except FileNotFoundError:
        logger.warning("Missing scoring table!")
        scoring_board = {
    "FP1": 9,
    "FP2": 3,
    "FP3": 1,
    "Q1ST": 9,
    "Q2ND": 3,
    "Q3RD": 1,
    "Q_BOTR": 18,
    "R1ST": 27,
    "R2ND": 9,
    "R3RD": 3,
    "R_BOTR": 54,
    "R_DOTD": 69,
    "R_FAST": 84,
    "R_DNF": 50
}
        with open(f'{SCORE_TABLE_PATH}score_table.json', 'w') as f:
            json.dump(scoring_board,f,indent=4)

    # users_db

    with open(f'{INVENTORY_PATH}users_db.json', 'r') as f:
        users_db = json.load(f)

    

    # collect users

    members = get_discord_members(ctx)
    logger.info(f"{members = }")

    # --- all resources are collected

    #
    # IMPORTANT: DNF IS STRING USING DRIVER_NAME KEY -> too much fuss in the for cycle
    #


    ## ready for evaluation  

    # for every user
    for user_name, user_id in members.items():
        user_guesses = guess_db_reversed[guess_db_reversed['user_name'] == user_name]
        user_guesses_unique = user_guesses.drop_duplicates(subset=['race_type'])
        # for every guess
        for (guessed_race_type, guessed_driver_name) in (zip(user_guesses_unique['race_type'], user_guesses_unique['driver_name'])):
            # for every race_type's row
            for race_type,driver_name in results.items():
                # for every race type
                if guessed_race_type == race_type:
                    #logger.info(f"{guessed_race_type} == {race_type}")
                    #logger.info(f"{guessed_driver_name} == {driver_name}")
                    # for every guess 
                    if guessed_driver_name == driver_name:
                        point = scoring_board[race_type] # each race_type's score
                        logger.info(f"MATCH! {user_name}: {race_type},{driver_name} - {point} point")
                        logger.info(f"{race_id = }")
                        if str(race_id) not in users_db[str(user_id)]["round_score"]:
                            users_db[str(user_id)]["round_score"][str(race_id)] = {}
                        if "date" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["date"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                        if "location" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["location"] = race_name
                        if "score_board" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["score_board"] = {}
                        # but not for points, to restrict overwriting guesses
                        users_db[str(user_id)]["round_score"][str(race_id)]["score_board"][race_type] = point # if not DNF
    
    with open(f'{INVENTORY_PATH}users_db.json', 'w') as f:
        json.dump(users_db,f,indent=4)

    logger.info("Dumped users_db")
                        
    await ctx.followup.send("Finished evaluating")

    logger.info("eval finished")

@bot.tree.command(name="date",description="-")    
async def setdate(interaction:Interaction, *, date_input:str):
    try:
        parsed_date = parse(date_input)
        if parsed_date:
            # set_date 2023 09 16
            await interaction.response.send_message(f"Race date set to: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Race date set to: {parsed_date.strftime('%Y-%m-%d %H:%M:%S')}")
            with open(f"{UPCOMING_DATE_PATH}upcoming_date","w") as f:
                f.write(parsed_date.strftime('%Y-%m-%d %H:%M:%S'))
        else:
            await interaction.response.send_message("Invalid date format. Please use a valid date format.")
    except Exception as e:
        await interaction.response.send_message(f"An error occurred: {str(e)}")

#--------< Additional Functions >----#

@bot.tree.command(name="showresults",description="-")
async def results(ctx:Interaction):
    results = f1_module.results_board
    await ctx.channel.send(f"For {f1_module.prev_race_name}:")
    pretty_json = json.dumps(results, indent=4)
    await ctx.response.send_message(pretty_json)


@bot.tree.command(name="todo",description="please do these tests")
async def todo(ctx:Interaction):
    tutorial = """
1. Check showresults if its correct
2. Guess as many as possible
3. Maybe try glitching it
"""
    await ctx.response.send_message(tutorial)

@bot.tree.command(name="rules",description="-")
async def rules(interaction:Interaction):
    rule_book = """
Rules for guessing:
1. find all the users who guessed (if didnt, out of game)
2. if more guesses under same race_type then latest matters.
3. if didnt guess in a race_type then doesnt get points
"""
    await interaction.response.send_message(rule_book)

@bot.tree.command(name="getlogs",description="-")
async def getlogs(interaction:Interaction, num_of_lines:int=500):
    """ send logs as pdf to report"""
    logger.info(f"getlogs with {num_of_lines} lines")
    try:
        with open(f"{LOGS_PATH}botlogs.log", 'r') as file:
            lines = file.readlines()[-(num_of_lines):]
    except Exception as e:
        logger.info(e)
    logger.info(f"read lines")
    with open(f"{LOGS_PATH}botlogs_extract.md", 'w') as file:
        for line in lines:
            file.write(line)
    logger.info(f"botlogs_extract.md populated")
    cmd = f'pandoc {LOGS_PATH}botlogs_extract.md -o {UPLOADS_PATH}botlogs_extract_{num_of_lines}.pdf'
    os.system(cmd)        
    await interaction.response.send_message(file=discord.File(UPLOADS_PATH+"botlogs_extract_"+str(num_of_lines)+".pdf"),delete_after=6)

    # only send back last N number of lines to reduce file size

@bot.tree.command(name="myguess",description="-")
async def myguess(ctx:discord.Interaction):
    with open(f"{INVENTORY_PATH}guess_db.json", "r") as f:
            guesses_database = json.load(f)
    user_guesses = f1_data.pd.DataFrame.from_dict(guesses_database, orient='index')
    user_guesses.reset_index(inplace=True)
    user_guesses.rename(columns={'index': 'time_stamp'}, inplace=True)
    user_guesses_reversed = user_guesses.iloc[::-1]
    
    cur_user = user_guesses_reversed[user_guesses_reversed['user_name'] == ctx.user.name]

    cur_user_unique = cur_user.drop_duplicates(subset=['race_type'])
    cur_user_unique.set_index('race_type', inplace=True)
    cur_user_unique = cur_user_unique.sort_values(by='race_type')
    logger.info(cur_user_unique)
    race_name = f1_module.get_next_race_id_and_name()["name"]
    with open(f"{UPLOADS_PATH}user_guesses_list.md",'w') as f:
        f.write(f"### {'&nbsp;'*11} {ctx.user.name}'s guesses for {race_name} {datetime.datetime.now().year}\n")
        f.write(cur_user_unique['driver_name'].to_markdown())
    
    cmd = f'pandoc {UPLOADS_PATH}user_guesses_list.md -o {UPLOADS_PATH}user_guesses_list.pdf'
    cmd2 = f'pdftoppm {UPLOADS_PATH}user_guesses_list.pdf {UPLOADS_PATH}user_guesses_list -png'
    cmd3 = f'convert {UPLOADS_PATH}user_guesses_list-1.png -crop 500x500+350+235 {UPLOADS_PATH}user_guesses_list_zoomed.png'
    os.system(cmd)
    os.system(cmd2)
    os.system(cmd3)

    await ctx.response.send_message(file=discord.File(f"{UPLOADS_PATH}user_guesses_list_zoomed.png"))

#--------< Funny Functions >----#

@bot.tree.command(name="whoami",description="-")
async def whoami(ctx:Interaction):
    await ctx.response.send_message(f"You are {ctx.user.name},\nHey <@{ctx.user.id}>")

@bot.tree.command(name="hello",description="-")
async def hello(ctx:Interaction):
    await ctx.response.send_message("Hello there")

@bot.tree.command(name="pina",description="fúú, te kibaszott perverz")
async def pina(ctx:Interaction):
    await ctx.response.send_message("Itt egy titkos pina csak neked: ()",ephemeral=True)

@bot.tree.command(name="fasz",description="fúú, te kibaszott perverz")
async def fasz(ctx:Interaction):
    await ctx.response.send_message("Itt egy titkos fasz csak neked: 8===Đ",ephemeral=True)

@bot.tree.command(name="jo_isten_kuldte_hozzank_le",description="-")
async def vitya(ctx:Interaction):
    await ctx.response.send_message(file=discord.File(UPLOADS_PATH+"vitya.png"))

@bot.tree.command(name="lajos",description="-")
async def lajos(ctx:Interaction, pia:str="palinka"):
    await ctx.response.defer()
    channel = bot.get_channel(CHANNEL_ID)
    logger.info("lajos már régen volt az neten bazdmeg")
    script = """- Szia Lajos. 👋
-       Szia bazdmeg! Kutyáidat sétáltatod?
- Hát bazdmeg
-                 Ilyen...ilyen szerelésbe?
- Hát miér milyenbe?
-           Miért nem öltözöl föl rendesen?
- Hát miér hát nem vagyok rendesen bazdmeg?
-                                Na jólvan.
- Most vettem fel bazdmeg délután!
-             Ilyen... hát kár volt bazdmeg
- Hát ja
-                            Na jólvan szia
- Szia 👋 """
    if pia == "palinka":
        for line in script.split('\n'):
            await channel.send(line)
    elif pia == "geci":
        await channel.send("|| Húh, uauháuúháúáúháúu mi az apád faszát hoztál te buzi? ||")
    await ctx.followup.send("---")

### UNSTABLE

@bot.tree.command(name="gyere",description="-")
async def join(ctx:Interaction):
    await ctx.response.defer()
    """Joins a voice channel"""
    if ctx.guild.voice_client is not None:
        return await ctx.guild.voice_client.move_to("General")
    channel = [chnl for chnl in ctx.guild.voice_channels][0]
    await channel.connect()
    await ctx.response.pong()

@bot.tree.command(name="halljuk",description="-")
async def play(ctx:Interaction, person:typing.Literal["lajos","hosszulajos","vitya","max","feri","hektor","kozso","furaferi"]):
    """Plays a file from the local filesystem"""
    await ctx.response.defer()
    song_list = {
        "lajos": f"{UPLOADS_PATH}szia_lajos.mp3",
        "hosszulajos": f"{UPLOADS_PATH}lajos_trim.mp3",
        "vitya": f"{UPLOADS_PATH}orban_plays.mp3",
        "max": f"{UPLOADS_PATH}verstappen.mp3",
        "feri": f"{UPLOADS_PATH}orban_plays_kard.mp3",
        "hektor": f"{UPLOADS_PATH}feljarok.mp3",
        "kozso": f"{UPLOADS_PATH}delfinek.mp3",
        "furaferi": f"{UPLOADS_PATH}kisfiu.mp3",
    }

    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song_list[person]))
    ctx.guild.voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
    await ctx.response.pong()

@bot.tree.command(name="naszia",description="-")
async def stop(ctx:Interaction):
    """Stops and disconnects the bot from voice"""
    ctx.guild.voice_client.cleanup()
    await ctx.guild.voice_client.disconnect()
    #await ctx.followup.send("---",ephemeral=True)

### UNSTABLE

def create_resources_dir():
    # create resources directory and subdirectories
    try:
        directory = "resources"
        path = os.path.join('./', directory)
        os.mkdir(path)
        print("Directory '% s' created" % directory)
    except FileExistsError:
        logger.info("Resources dir already exists")

#----< Main Function Init >----#


if __name__ == "__main__":
    pass