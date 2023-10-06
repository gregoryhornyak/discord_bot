# This example requires the 'members' and 'message_content' privileged intents to function, therefore using intents=discord.Intents.all()

#----< Imports >----#

import discord
from discord.ext import commands

import datetime
import os

import typing

from discord.interactions import Interaction

from include.logging_manager import logger
from include.constants import *
import include.f1_data_fetcher as f1_data
import include.database_manager as db_man

import asyncio
from dateutil.parser import parse
import subprocess

from PIL import Image, ImageFont, ImageDraw
import random
import calendar

##
## TODO
##

#----< Working directory >----#

current_directory = os.getcwd()
logger.info(f"{current_directory = }")

#----< Bot init >----#

bot = commands.Bot(command_prefix="/",intents=discord.Intents.all())

f1_module = f1_data.F1DataFetcher()

@bot.event
async def on_message(ctx:Interaction):
    if ctx.author.name != "lord_maldonado":
        did_swear = [item for item in SWEAR_WORDS if item in ctx.content]
        if did_swear:
            await ctx.channel.send(random.choice(BLACK_LISTED_PHRASES))

# implement pause between upgrade shutdowns
# read a manifest on how many minutes to stop for

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user}')
    bot.tree.copy_global_to(guild=discord.Object(id=SERVER_ID))
    await bot.tree.sync(guild=discord.Object(id=SERVER_ID))
    channel = bot.get_channel(CHANNEL_ID)
    #* MESSAGE DELETE SECTION
    history_gen = channel.history(limit=1)
    list_of_messages = []
    async for result in history_gen:
        message = await channel.fetch_message(result.id)
        for line in [BOT_SHUTDOWN_UPGRD_MESSAGE,BOT_START_DETAILS_MESSAGE_LINE,BOT_START_SHORT_MESSAGE,"Bot started"]:
            if line in message.content:
                list_of_messages.append(message)
    await channel.delete_messages(list_of_messages,reason="Remove update-alert-message")

    # create lock file if not exists
    locked = {"locked":False}
    try:
        with open(LOCK_FILE_PATH,"r") as f:
            locked = json.load(f)
    except (json.decoder.JSONDecodeError, FileNotFoundError) as e:
        logger.error(e)
        with open(LOCK_FILE_PATH,"w") as f:
            json.dump(locked,f,indent=4)
    finally:
        logger.info(f"{locked = }")

    man_version = get_manifest_version_info()

    with open(f"{MANIFEST_PATH}", "r") as f:
        manifest_info = json.load(f)

    boot_message = f1_data.re.sub(r'bot_name', manifest_info['bot_name'], BOT_START_DETAILS_MESSAGE)
    boot_message = f1_data.re.sub(r'version', manifest_info['version'], boot_message)
    boot_message = f1_data.re.sub(r'latest_ver', man_version, boot_message)
    boot_message = f1_data.re.sub(r'latest_update', manifest_info['latest'], boot_message)

    await channel.send("Bot started",silent=True)

    await bot.change_presence(activity=discord.Game(name=f"in {BOT_STATE} mode"))

    await asyncio.sleep(6)

    await channel.last_message.edit(content=BOT_START_SHORT_MESSAGE)

    await schedule_daily_message()


@bot.tree.command(name="status",description="get bot status")
async def bot_state(ctx:Interaction):
    await ctx.response.send_message(f"{BOT_STATE = }")

def get_manifest_version_info():
    git_link = "https://raw.githubusercontent.com/gregoryhornyak/discord_bot/master/docs/manifest/manifest.json"
    manifest = f1_data.requests.get(git_link).json()
    return manifest['version']
    
async def schedule_daily_message():
    loop_counter = 0
    while True:
        channel = bot.get_channel(CHANNEL_ID)
        now = datetime.datetime.now()

        # do daily fetch
        if now.hour == 6 and now.minute == 15:
            f1_module.daily_fetch()

        next_grand_prix_events_time = {race_type: datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S.%f') for race_type,time in f1_module.next_grand_prix_events.items()}
        #logger.info(f"{next_grand_prix_events_time = }")    

        for r_t, time in next_grand_prix_events_time.items():
            one_day_later = datetime.timedelta(days = 1)
            delta = now.replace(second=0, microsecond=0) + one_day_later
            if time == delta and time.hour == delta.hour:
                await channel.send(f"{r_t} starts in 1 day!")
            if now.hour+2 == time.hour:
                if now.minute == time.minute:
                    await channel.send(f"{r_t} starts in 2 hours!") 
            if now.hour+1 == time.hour:
                if now.minute == time.minute:
                    await channel.send(f"{channel.guild.default_role} {r_t} starts in **1 hour**! Take your guesses!")
            if now.day == time.day and now.hour == time.hour:
                if now.minute == time.minute:
                    await channel.send(f"{channel.guild.default_role} Guessing phase is over for {r_t}!")
                    #lock_guess(r_t)
                    
                    f1_module.guess_schedule[r_t] = True

        loop_counter += 1
        await asyncio.sleep(55)

@bot.tree.command(name="upgrade",description="long")
async def upgrade(interaction:Interaction,password:str):
    """reboots the whole bot, and updates it from Github"""
    password_stored = ""
    with open(f"{PASSW_PATH}",'r') as f:
        password_stored = f.read()
    if password!=password_stored:
        await interaction.response.send_message("Wrong password")
        return 0
    logger.info("BOT SHUTDOWN")
    await interaction.response.send_message(BOT_SHUTDOWN_UPGRD_MESSAGE)
    await bot.close()

# function to get every racing date -> save to file -> update alert 

def get_discord_members(ctx:Interaction): # dont change it
    user_info = {}
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            user_info[member.name] = member.id
    return user_info

async def save_discord_members_pics(ctx:Interaction) -> list: # dont change it
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            logger.debug(f"{member.name}")
            try:
                await member.avatar.save(f"{PROFILE_PICS_PATH}{member.name}.png")
            except AttributeError:
                await member.default_avatar.save(f"{PROFILE_PICS_PATH}{member.name}.png")


@bot.tree.command(name="guess",description="-")
async def guess(ctx:discord.Interaction): # Q: making the dropdown box into a slash command is a good option?
    """Allows the user to make a guess"""
    await ctx.response.defer(ephemeral=True)
    
    #await channel.send("Fetching has begun... may take a while",delete_after=1)

    # save the data into a file, to avoid long fetching
    drivers_info = f1_module.get_drivers_details()
    next_race_id = f1_module.next_race_details['id']
    next_race_name = f1_module.next_race_details['name']
    race_types_list = f1_module.get_race_types()
    logger.warning(f"{race_types_list = }")

    select_race = discord.ui.Select(placeholder="Choose a race!",
                                    options=[discord.SelectOption(
                                        label=race_name, description=None) for race_name in race_types_list if race_name!="R_DNF"])
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
        logger.info(f"{name}: {select_race.values[0]} - {select_driver.values[0]} for {next_race_name.capitalize()}")
        db_man.save_guess(name=name,
                          id=id,
                          select_race=select_race.values[0],
                          select_driver=select_driver.values[0],
                          next_race_id=next_race_id) # dnf=False
        await sub_interaction.response.send_message(f"{name}: {select_race.values[0]} - {select_driver.values[0]} for {next_race_name.capitalize()}",silent=True)

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback

    message = f"Guess for {next_race_name} {datetime.datetime.now().year}\n*For Race DNF, call '/dnf'*\n**(use this form for multiple guesses)**"
    await ctx.followup.send(content=message, view=theView)

#schedule_2023 = "https://www.formula1.com/en/latest/article.formula-1-update-on-the-2023-calendar.4pTQzihtKTiegogmNX5XrP.html"

@bot.tree.command(name="dnf",description="guess num of dnf")
async def dnf(interaction: discord.Interaction, count: int):
    next_race_id = f1_module.next_race_details['id']
    next_race_name = f1_module.next_race_details['name']
    count = abs(count)
    db_man.save_guess(name=interaction.user.name,id=interaction.user.id,select_race="R_DNF",select_driver=count,dnf=True,next_race_id=next_race_id)
    await interaction.response.send_message(f'You guessed {count} number of DNF(s)', ephemeral=True)
    logger.info(f"{interaction.user.name}: R_DNF - {count} for {next_race_name.capitalize()}")

@bot.tree.command(name="eval",description="-")
async def eval(ctx:Interaction):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    channel = bot.get_channel(CHANNEL_ID)

    # FETCHING

    # save dataframes into data/fetched_data every morning

    # headers: | Pos No Driver Car Laps Time/Retired PTS
    await ctx.response.defer()
    scores_json = f1_module.get_all_results()

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
        with open(f"{GUESS_DB_PATH}", "r") as f:
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

    race_id:int = f1_module.prev_race_details['id']
    race_name:str = f1_module.prev_race_details['name']

    # results - official results
    # existence assured by f1_module
    with open(f"{RESULTS_PATH}", "r") as f:
        results = json.load(f)
    results = results[race_id]

    # collect score table entries
    try:
        with open(f'{SCORE_TABLE_PATH}', 'r') as f:
            scoring_board = json.load(f)
    except FileNotFoundError:
        logger.warning("Missing scoring table!")
        scoring_board = {
        "FP1": 9,
        "FP2": 3,
        "FP3": 1,
        "SH": 2,
        "S": 3,
        "Q1": 9,
        "Q2": 3,
        "Q3": 1,
        "Q_BOTR": 18,
        "R1": 27,
        "R2": 9,
        "R3": 3,
        "R_BOTR": 54,
        "R_DOTD": 69,
        "R_FAST": 84,
        "R_DNF": 50
        }
        with open(f'{SCORE_TABLE_PATH}', 'w') as f:
            json.dump(scoring_board,f,indent=4)

    # users_db
    users_db = {}
    try:
        with open(f'{USERS_DB_PATH}', 'r') as f:
            users_db = json.load(f)
    except FileNotFoundError:
        logger.warning("NO USERS_DB_JSON")
        with open(f'{USERS_DB_PATH}', 'w') as f:
            json.dump(users_db,f,indent=4)
    

    # collect users

    members = get_discord_members(ctx)

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
                    # for every guess 
                    if guessed_driver_name == driver_name:
                        point = scoring_board[race_type] # each race_type's score
                        logger.info(f"{user_name}: {race_type},{driver_name} - {point} point")
                        #await channel.send(f"{user_name}: {race_type} - {driver_name} -> {point} point")
                        if str(user_id) not in users_db:                            
                            users_db[str(user_id)] = {"user_name": user_name,"round_score": {},"total_points": 0}
                        if str(race_id) not in users_db[str(user_id)]["round_score"]:
                            users_db[str(user_id)]["round_score"][str(race_id)] = {}
                        if "date" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["date"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                        if "location" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["location"] = race_name
                        if "evaluated" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["location"] = "False"
                        if "score_board" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["score_board"] = {}
                        # but not change for points, to restrict overwriting guesses
                        users_db[str(user_id)]["round_score"][str(race_id)]["score_board"][race_type] = point # if not DNF
                        
    await ctx.followup.send("Finished evaluating")

    logger.info("eval finished")

    # sum up the points
    leader_board = {}
    for the_rest in users_db.values():
        local_score = 0
        for race_list in the_rest["round_score"].values():
            for key, race_details in race_list.items():
                if key == "score_board":
                    for point in race_details.values():
                        local_score += int(point)
        the_rest["total_points"] = local_score
        leader_board[the_rest["user_name"]] = local_score

    with open(f'{USERS_DB_PATH}', 'w') as f:
        json.dump(users_db,f,indent=4)

    logger.info("Dumped users_db")

    logger.debug(f"{leader_board = }")
    leader_board = dict(sorted(leader_board.items(), key=lambda item: item[1], reverse=True))
    profiles = [str(PROFILE_PICS_PATH+member_name+".png") for member_name in leader_board.keys()]
    await save_discord_members_pics(ctx)
    winner_name = "NOONE"
    if profiles:
        winner_name = profiles[0].split('/')[-1].split('.')[0]
    logger.info(f"{winner_name = }")
    if len(profiles) > 1:
        create_podium(profiles[0],profiles[1],profiles[2],race_name.capitalize(),str(datetime.datetime.now().year),winner_name)
    #await ctx.channel.send("Finished leaderboard")
    #await ctx.channel.send(file=discord.File("resources/uploads/winners.png"))
    
def create_podium(place_1,place_2,place_3,race_name,year,winner_name):

    place1 = Image.open(place_1)
    place2 = Image.open(place_2)
    place3 = Image.open(place_3)
    new_size1 = (300, 300)
    new_size2 = (230, 230)
    new_size3 = (180, 180)
    image1 = place1.resize(new_size1)
    image2 = place2.resize(new_size2)
    image3 = place3.resize(new_size3)
    background_image = Image.open('resources/uploads/winners_stand.png')
    background_image = background_image.convert('RGB')
    combined_image = Image.new('RGB', background_image.size)
    combined_image.paste(background_image, (0, 0))
    # 1256x702
    coord_image1 = (670-int(new_size1[0]/2),135)  # Coordinates for image1
    coord_image2 = (260-int(new_size2[0]/2), 220)  # Coordinates for image2
    coord_image3 = (1055-int(new_size2[0]/2), 288)  # Coordinates for image3
    combined_image.paste(image1, coord_image1)
    combined_image.paste(image2, coord_image2)
    combined_image.paste(image3, coord_image3)

    grat = random.choice(GRATULATION_PHRASES)

    text = f"{grat} {winner_name}!   ({race_name}, {year})"
    #font = ImageFont.truetype("arial.ttf", size=36)
    position = (300, 634)
    text_color = (0, 0, 0)
    combined_image.save('resources/uploads/winners.png')
    image = Image.open('resources/uploads/winners.png')
    draw = ImageDraw.Draw(image)
    font_size = 40
    font = ImageFont.truetype("resources/uploads/Autography.otf", font_size)
    draw.text(position, text, fill=text_color, font=font)
    image.save('resources/uploads/winners.png')


@bot.tree.command(name="bonus",description="-")
async def bonus(ctx:Interaction):
    await ctx.response.send_message(file=discord.File(UPLOADS_PATH+"winners.png"))

#--------< Additional Functions >----#

@bot.tree.command(name="showresults",description="-")
async def results(ctx:Interaction):
    results = f1_module.results_board
    logger.warning(f"{f1_module.prev_race_details['name'] = }")
    await ctx.channel.send(f"For {f1_module.prev_race_details['name']}:")
    pretty_json = json.dumps(results, indent=4)
    await ctx.response.send_message(pretty_json)


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
        with open(f"{LOGS_PATH}", 'r') as file:
            lines = file.readlines()[-(num_of_lines):]
    except Exception as e:
        logger.info(e)
    logger.info(f"read lines")
    with open(f"{BOT_LOGS_EXT_MD_PATH}", 'w') as file:
        for line in lines:
            file.write(line)
    logger.info(f"botlogs_extract.md populated")
    cmd = f'pandoc {BOT_LOGS_EXT_MD_PATH} -o {BOT_LOGS_EXT_PDF_PATH}_{num_of_lines}.pdf'
    os.system(cmd)        
    await interaction.response.send_message(file=discord.File(BOT_LOGS_EXT_PDF_PATH+"_"+str(num_of_lines)+".pdf"),delete_after=6)

    # only send back last N number of lines to reduce file size

@bot.tree.command(name="myguesses",description="-")
async def myguess(ctx:discord.Interaction,username:str=""):
    with open(f"{GUESS_DB_PATH}", "r") as f:
            guesses_database = json.load(f)
    user_guesses = f1_data.pd.DataFrame.from_dict(guesses_database, orient='index')
    user_guesses.reset_index(inplace=True)
    user_guesses.rename(columns={'index': 'time_stamp'}, inplace=True)
    user_guesses_reversed = user_guesses.iloc[::-1]
    logger.info(f"{get_discord_members(ctx=ctx) = }")
    user_name = ""
    if username:
        user_name = username
    else:   
        user_name = ctx.user.name
    cur_user = user_guesses_reversed[user_guesses_reversed['user_name'] == user_name]

    race_name = f1_module.next_race_details["name"]
    next_race_id = f1_module.next_race_details["id"]
    cur_user_unique = cur_user.drop_duplicates(subset=['race_type'])
    cur_user_unique.set_index('race_type', inplace=True)
    cur_user_unique = cur_user_unique.sort_values(by='race_type')
    cur_user_unique = cur_user_unique[cur_user_unique['race_id'] == next_race_id]
    logger.info(cur_user_unique)
    
    with open(f"{USER_GUESS_HISTORY_PATH}",'w') as f:
        f.write(f"### {'&nbsp;'*11} {user_name}'s guesses for {race_name} {datetime.datetime.now().year}\n")
        f.write(cur_user_unique['driver_name'].to_markdown())
    
    cmd = f'pandoc {USER_GUESS_HISTORY_PATH} -o {USER_GUESS_HISTORY_PDF_PATH}.pdf'
    cmd2 = f'pdftoppm {USER_GUESS_HISTORY_PDF_PATH}.pdf {USER_GUESS_HISTORY_PDF_PATH} -png'
    cmd3 = f'convert {USER_GUESS_HISTORY_PDF_PATH}-1.png -crop 500x500+350+235 {USER_GUESS_HISTORY_PDF_PATH}_zoomed.png'
    os.system(cmd)
    os.system(cmd2)
    os.system(cmd3)

    await ctx.response.send_message(file=discord.File(f"{USER_GUESS_HISTORY_PDF_PATH}_zoomed.png"))

@bot.tree.command(name="mypoints",description="-")
async def mypoints(ctx:discord.Interaction,username:str=""):
    users_db = {}
    user_name = ""
    if username:
        user_name = username
    else:   
        user_name = ctx.user.name
    with open(f"{USERS_DB_PATH}", "r") as f:
            users_db = json.load(f)
    cur_user_db = users_db[str(ctx.user.id)]
    prev_race_id = f1_module.prev_race_details["id"]
    prev_race_name = f1_module.prev_race_details["name"]
    user_score = cur_user_db["round_score"][prev_race_id]["score_board"]
    user_score_df = f1_data.pd.DataFrame.from_dict(user_score,orient='index')
    user_score_df.rename(columns={0: 'Point'}, inplace=True)
    logger.info(f"{user_name = } {prev_race_name = } {user_score_df = }")
    with open(f"{USER_POINT_HISTORY_PATH}",'w') as f:
        f.write(f"### {'&nbsp;'*11} {user_name}'s score for {prev_race_name} {datetime.datetime.now().year}\n")
        f.write(user_score_df.to_markdown())
    cmd = f'pandoc {USER_POINT_HISTORY_PATH} -o {USER_POINT_HISTORY_PDF_PATH}.pdf'
    cmd2 = f'pdftoppm {USER_POINT_HISTORY_PDF_PATH}.pdf {USER_POINT_HISTORY_PDF_PATH} -png'
    cmd3 = f'convert {USER_POINT_HISTORY_PDF_PATH}-1.png -crop 500x500+350+235 {USER_POINT_HISTORY_PDF_PATH}_zoomed.png'
    os.system(cmd)
    os.system(cmd2)
    os.system(cmd3)
    await ctx.response.send_message(file=discord.File(f"{USER_POINT_HISTORY_PDF_PATH}_zoomed.png"))

#--------< Funny Functions aka Easter Eggs >----#

@bot.tree.command(name="dadjoke",description="-")
async def dadjoke(ctx:Interaction):
    cmd = 'curl -H "Accept: application/json" https://icanhazdadjoke.com/'
    output = subprocess.check_output(cmd, shell=True,text=True)
    joke_json = json.loads(output)
    await ctx.response.send_message(f'Dad joke of the day:\n{joke_json["joke"]}')

@bot.tree.command(name="whoami",description="-")
async def whoami(ctx:Interaction):
    await ctx.response.send_message(f"You are {ctx.user.name},\nHey <@{ctx.user.id}>")

@bot.tree.command(name="info",description="-")
async def info(ctx:Interaction):
    # export this dict compr to F1_module as func
    next_event_details = {r_t: datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S.%f') for r_t,time in f1_module.next_grand_prix_events.items()}

    descr = f"The bot is in **{BOT_STATE}** mode.\n"
    disp_minute = ""
    
    for r_t,time in next_event_details.items():
        if time.minute < 10:
            disp_minute = str(time.minute)+"0"
        else:
            disp_minute = str(time.minute)
        descr += f"{time.day} {calendar.month_abbr[int(time.month)]}, {time.hour}:{disp_minute} - {r_t}\n"
    embed=discord.Embed(colour=0xFFFFFF,title="Race Information",description=descr)
    await ctx.response.send_message(embed=embed)

@bot.tree.command(name="hello",description="-")
async def hello(ctx:Interaction):
    await ctx.response.send_message(f"Hello there! {ctx.guild.default_role}")

@bot.tree.command(name="help",description="-")
async def embed_test(ctx:Interaction):
    descr = f"First, take your guesses by **/guess**\n\
    Then wait until the race completes\n\
    Finally evaluate your score by **/eval**\n\
    In the meanwhile,\n\
    you can see your guess by **/myguesses**\n\
    and you can see your point by **/mypoints**\n\
    And of course invoke many *funny* commands as well\n\
    \nGood luck! 😁🏁"
    embed=discord.Embed(title="Tutorial",
                        description=descr,
                        color=0xFF5733)
    await ctx.response.send_message(embed=embed)

@bot.tree.command(name="pina",description="fúú, te kibaszott perverz")
async def pina(ctx:Interaction):
    await ctx.response.send_message("Itt egy titkos pina csak neked: || () ||",ephemeral=True)

@bot.tree.command(name="fasz",description="fúú, te kibaszott perverz")
async def fasz(ctx:Interaction):
    await ctx.response.send_message("Itt egy titkos fasz csak neked: || 8===Đ ||",ephemeral=True)

@bot.tree.command(name="jo_isten_kuldte_hozzank_le",description="-")
async def vitya(ctx:Interaction):
    await ctx.response.send_message(file=discord.File(UPLOADS_PATH+"vitya.png"),silent=True)

@bot.tree.command(name="lajos",description="-")
async def lajos(ctx:Interaction, pia:str="palinka"):
    await ctx.response.defer()
    channel = bot.get_channel(CHANNEL_ID)
    logger.info("lajos már régen volt az neten bazdmeg")
    script = f"""- Szia Lajos. 👋
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
            await channel.send(line,silent=True)
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
    await ctx.guild.voice_client.disconnect()
    #await ctx.followup.send("---",ephemeral=True)



#----< Main Function Init >----#

if __name__ == "__main__":
    logger.warning("LOCAL FUNCTION RUNNING")
    pass