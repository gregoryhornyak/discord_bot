#----< Imports >----#

import discord
from discord.ext import commands

import datetime
import os

import typing

from discord.interactions import Interaction

from include.logging_manager import logger
from include.constants import *
import include.f1_data_manager as f1_data
import include.database_manager as db_man

import asyncio
from dateutil.parser import parse
import subprocess

from PIL import Image, ImageFont, ImageDraw
import random
import calendar

"""
todo:

- the bot should run automates tests every first bootup of the day:
  - check databases, requests, connection, modules, dependencies

"""

#----< Bot init >----#

bot = commands.Bot(command_prefix="/",intents=discord.Intents.all())

f1_module = f1_data.F1DataFetcher()

@bot.event
async def on_ready():
    logger.info(f'Logging in as {bot.user}')
    # synchronise commands globally
    with open(f"{SERVER_CHANNEL_ID_PATH}","r") as f:
        discord_data = json.load(f)
    bot.tree.copy_global_to(guild=discord.Object(id=discord_data["SERVER_ID"]))
    await bot.tree.sync(guild=discord.Object(id=discord_data["SERVER_ID"]))
    channel = bot.get_channel(discord_data["CHANNEL_ID"])
    
    await channel.send("Bot started",silent=True)

    await bot.change_presence(activity=discord.Game(name=f"in {BOT_STATE} mode"))

    #await channel.last_message.edit(content=BOT_START_SHORT_MESSAGE)

    # start agents
    await notification_agent()
    #await guess_agent()


@bot.event
async def on_message(ctx:Interaction):
    if ctx.author.name != "lord_maldonado":
        # search any swear words in the messages
        did_swear = [item for item in SWEAR_WORDS if item in ctx.content.lower()]
        if did_swear:
            await ctx.channel.send(random.choice(BLACK_LISTED_PHRASES))


@bot.tree.command(name="status",description="get bot's current state")
async def bot_state(ctx:Interaction):
    next_event_details = f1_module.next_grand_prix_events
    now = datetime.datetime.strftime(datetime.datetime.now,"%Y-%m-%d %H:%M:%S.%f")

    descr = f"The bot is in **{BOT_STATE}** mode.\n"
    now = datetime.datetime.now()
    prev_race_details = f1_module.prev_gp_details
    descr += f"⏪ {prev_race_details['name']}({prev_race_details['id']})\n"
    next_race_details = f1_module.next_gp_details
    descr += f"❎ Guessing for \n{next_race_details['name']}({next_race_details['id']})\n"
    descr += f"⏩ {next_race_details['name']}({next_race_details['id']})\n"

    bot_current_state = {}
    with open(STATE_FILE_PATH,"r") as f:
        bot_current_state = json.load(f)

    for raceid in ["raceID_1","raceID_2","raceID_3"]:
        racetime = bot_current_state[raceid]["date"]
        if datetime.datetime.strptime(racetime,'%Y-%m-%d %H:%M:%S.%f') <= now:
            bot_current_state[raceid]["when"] = "past"
        else:
            bot_current_state[raceid]["when"] = "future"

    embed=discord.Embed(colour=0xFFFFFF,title="Bot state info",description=descr)
    await ctx.response.send_message(embed=embed)
    
async def notification_agent():
    with open(f"{SERVER_CHANNEL_ID_PATH}","r") as f:
        discord_data = json.load(f)
    loop_counter = 0
    while True:
        channel = bot.get_channel(discord_data["CHANNEL_ID"])
        now = datetime.datetime.now()

        # do daily fetch
        if now.hour == 8 and now.minute == 20:
            f1_module.daily_fetch()
            pass

        next_grand_prix_events_time = {category: datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S.%f') for category,time in f1_module.next_gp_details["sessions"].items()}  
        delta = now.replace(second=0, microsecond=0) + datetime.timedelta(days = 1)
        for r_t, time in next_grand_prix_events_time.items():
            if time.month == delta.month and time.day == delta.day and time.hour == delta.hour and time.minute == delta.minute:
                await channel.send(f"{r_t} starts in 1 day!") # seems oke
            if now.month == time.month and now.day == time.day and now.hour+2 == time.hour and now.minute == time.minute:
                await channel.send(f"{r_t} starts in 2 hours!") 
            if now.month == time.month and now.day == time.day and now.hour+1 == time.hour and now.minute == time.minute:
                await channel.send(f"{channel.guild.default_role} {r_t} starts in **1 hour**! Take your guesses!")
            if now.month == time.month and now.day == time.day and now.hour == time.hour and now.minute == time.minute:
                await channel.send(f"{channel.guild.default_role} Guessing phase is over for {r_t}!")

        loop_counter += 1
        await asyncio.sleep(ALERT_CHECK_DELAY)

async def guess_agent():
    """stops guessing after deadline"""
    pass

@bot.tree.command(name="upgrade",description="ADMIN - reboots and updates bot")
async def upgrade(interaction:Interaction,password:str):    
    """reboots the whole bot, and updates it from Github"""
    with open(f"{PASSW_PATH}",'r') as f:
        found_pw = f.read().strip()
        logger.info(f"{password}!={found_pw} is {password!=found_pw}")
        if password!=found_pw:
            await interaction.response.send_message("Wrong password")
            return 0
    logger.info("Bot shuts down and upgrades")
    await interaction.response.send_message(BOT_SHUTDOWN_UPGRD_MESSAGE)
    await bot.close()

def get_discord_members(ctx:Interaction): # dont change it
    user_info = {}
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            user_info[member.name] = member.id
    return user_info

async def save_discord_members_pics(ctx:Interaction) -> list: # dont change it
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            try:
                await member.avatar.save(f"{PROFILE_PICS_PATH}{member.name}.png")
            except AttributeError:
                await member.default_avatar.save(f"{PROFILE_PICS_PATH}{member.name}.png")

@bot.tree.command(name="guess",description="Make a guess for a category and a driver")
async def guess(ctx:discord.Interaction): # Q: making the dropdown box into a slash command is a good option?
    """Allows the user to make a guess"""
    await ctx.response.defer(ephemeral=True)

    drivers_info = f1_module.get_drivers_details() #* could be cached
    next_race_id = f1_module.get_next_gp_id()
    next_race_name = f1_module.get_next_gp_name()
    categories_list = f1_module.get_categories()
    logger.info(f"{categories_list = } {drivers_info = }")

    select_race = discord.ui.Select(placeholder="Choose a category!",
                                    options=[discord.SelectOption(
                                        label=category, description=None) for category in categories_list if category!="R_DNF"])
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

@bot.tree.command(name="dnf",description="Guess number of DNF")
async def dnf(interaction: discord.Interaction, count: int):
    next_race_id = f1_module.next_gp_details['id']
    next_race_name = f1_module.next_gp_details['name']
    count = abs(count)
    db_man.save_guess(name=interaction.user.name,id=interaction.user.id,select_race="R_DNF",select_driver=count,dnf=True,next_race_id=next_race_id)
    await interaction.response.send_message(f'You guessed {count} number of DNF(s)', ephemeral=True)
    logger.info(f"{interaction.user.name}: R_DNF - {count} for {next_race_name.capitalize()}")

@bot.tree.command(name="eval",description="-")
async def eval(ctx:Interaction):
    """read the results, and compare them with the guesses
    could only happen after the race"""
    with open(f"{SERVER_CHANNEL_ID_PATH}","r") as f:
        discord_data = json.load(f)
    channel = bot.get_channel(discord_data["CHANNEL_ID"])

    await ctx.response.defer()

    scores_json = {}
    with open(f"{SCORE_TABLE_PATH}","r") as f:
        scores_json = json.load(f)

    # EVALUATING

    # 1. find all the users who guessed (if didnt, out of game)
    # 2. if more guesses under same category then latest matters.
    # 3. if didnt guess in a category then doesn't get points
    # 4. assign score board value

    # files needed:
    # - guess_db
    # - prev_gp_details.results
    # - score_table
    # - users_db

    # guess_db - users' guesses on race results
    try:
        with open(f"{GUESS_DB_PATH}", "r") as f:
            guess_db = json.load(f)
    except FileNotFoundError:
        logger.info("Missing guess_db.json")
        ctx.channel.send("There are no guesses yet")
        return 0

    # does it need to be transformed into a dataframe?
    guess_db = f1_data.pd.DataFrame.from_dict(guess_db, orient='index')
    guess_db.reset_index(inplace=True)
    guess_db.rename(columns={'index': 'time_stamp'}, inplace=True)
    guess_db_reversed = guess_db.iloc[::-1]
    #logger.info(f"{guess_db_reversed = }")

    # f1 data

    race_id = f1_module.get_prev_gp_id()
    race_name = f1_module.get_prev_gp_name()

    # results - official results
    # existence assured by f1_module
    results = f1_module.get_all_results()

    # collect score table entries
    try:
        with open(f'{SCORE_TABLE_PATH}', 'r') as f:
            scoring_board = json.load(f)
    except FileNotFoundError:
        logger.warning("Missing scoring table!")
        scoring_board = {
        "FP1": 3,
        "FP2": 2,
        "FP3": 1,
        "SH": 2,
        "S": 1,
        "Q1": 3,
        "Q2": 2,
        "Q3": 1,
        "Q_BOTR": 1,
        "R1": 5,
        "R2": 3,
        "R3": 2,
        "R_BOTR": 1,
        "DOTD": 1,
        "R_FAST": 1,
        "R_DNF": 1
        }
        logger.info("Creating score_table.json")
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

    logger.info(f"{f1_module.prev_gp_details['id'] = }")
    logger.info(f"{f1_module.next_gp_details['id'] = }")

    ## ready for evaluation  

    # for every user
    for user_name, user_id in members.items():
        user_guesses = guess_db_reversed[guess_db_reversed['user_name'] == user_name]
        user_guesses_unique = user_guesses.drop_duplicates(subset=['category'])
        # for every guess
        for (guessed_category, guessed_driver_name) in (zip(user_guesses_unique['category'], user_guesses_unique['driver_name'])):
            # for every category's row
            for category,driver_name in results.items():
                # for every race type
                if guessed_category == category:
                    # for every guess 
                    if guessed_driver_name == driver_name:
                        if str(category) in scoring_board:                            
                            point = scoring_board[category] # each category's score
                        else:
                            logger.info("EVAL: missing race type")
                        logger.info(f"{user_name}: {category},{driver_name} - {point} point")
                        #await channel.send(f"{user_name}: {category} - {driver_name} -> {point} point")

                        # check if user_guesses_unique["time_stamp"] valid

                        logger.debug(f"{race_name = }")

                        if str(user_id) not in users_db:                            
                            users_db[str(user_id)] = {"user_name": user_name,"round_score": {},"total_points": 0}
                        if str(race_id) not in users_db[str(user_id)]["round_score"]:
                            users_db[str(user_id)]["round_score"][str(race_id)] = {}
                        if "date" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["date"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                        if "location" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["location"] = race_name
                        """
                        if "evaluated" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["evaluated"] = "False"
                        """
                        if "score_board" not in users_db[str(user_id)]["round_score"][str(race_id)]:
                            users_db[str(user_id)]["round_score"][str(race_id)]["score_board"] = {}
                        # but not change for points, to restrict overwriting guesses
                        users_db[str(user_id)]["round_score"][str(race_id)]["score_board"][category] = point # if not DNF
                        
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

    logger.info("Saved users_db")

    leader_board = dict(sorted(leader_board.items(), key=lambda item: item[1], reverse=True))

    logger.debug(f"{leader_board = }")

    descr = ""
    for index, (name, score) in enumerate(leader_board.items()):
        descr += f"{index}. {name} - {score} pts\n"

    embed=discord.Embed(colour=0xFFFFFF,title="LEADERBOARD",description=descr)
    #await ctx.response.send_message()

    await ctx.followup.send(embed=embed)

    leader_board = dict(sorted(leader_board.items(), key=lambda item: item[1], reverse=True))
    profiles = [str(PROFILE_PICS_PATH+member_name+".png") for member_name in leader_board.keys()]
    await save_discord_members_pics(ctx)
    winner_name = "NOONE"
    if profiles:
        winner_name = profiles[0].split('/')[-1].split('.')[0]
    logger.info(f"{winner_name = }")
    #if len(profiles) > 1:
     #   create_podium(profiles[0],profiles[1],profiles[2],race_name.capitalize(),str(datetime.datetime.now().year),winner_name)
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
    logger.info("Team photo requested")

#--------< Additional Functions >----#

@bot.tree.command(name="showresults",description="**DEBUG**")
async def results(ctx:Interaction):
    results = f1_module.results_board
    logger.warning(f"{f1_module.prev_gp_details['name'] = }")
    await ctx.channel.send(f"For {f1_module.prev_gp_details['name']}:")
    pretty_json = json.dumps(results, indent=4)
    await ctx.channel.send(pretty_json)


@bot.tree.command(name="rules",description="-")
async def rules(interaction:Interaction):
    rule_book = """
Rules for guessing:
1. find all the users who guessed (if didnt, out of game).
2. if more guesses under same category then latest matters.
3. if didnt guess in a category then doesn't get points.
"""
    await interaction.response.send_message(rule_book)

@bot.tree.command(name="getlogs",description="ADMIN - show logs ")
async def getlogs(ctx:discord.Interaction, num_of_lines:int=500):
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
    cmd = f'pandoc --pdf-engine=xelatex --variable "monofont:docs/FreeMono.otf" {BOT_LOGS_EXT_MD_PATH} -o {BOT_LOGS_EXT_PDF_PATH}'
    os.system(cmd)    
    logger.info(f'sending {BOT_LOGS_EXT_PDF_PATH+"_"+str(num_of_lines)+".pdf"}')
    await ctx.response.send_message(file=discord.File(BOT_LOGS_EXT_PDF_PATH),delete_after=6)

    # only send back last N number of lines to reduce file size

@bot.tree.command(name="myguesses",description="Show user's guesses for next grand prix")
async def myguess(ctx:discord.Interaction,username:str=""):
    with open(f"{GUESS_DB_PATH}", "r") as f:
            guesses_database = json.load(f)
    user_guesses = f1_data.pd.DataFrame.from_dict(guesses_database, orient='index')
    user_guesses.reset_index(inplace=True)
    user_guesses.rename(columns={'index': 'time_stamp'}, inplace=True)
    user_guesses_reversed = user_guesses.iloc[::-1]
    user_name = ""
    if username:
        user_name = username
    else:   
        user_name = ctx.user.name
    cur_user = user_guesses_reversed[user_guesses_reversed['user_name'] == user_name]

    race_name = f1_module.get_next_gp_name()
    next_race_id = f1_module.get_next_gp_id()
    cur_user_unique = cur_user.drop_duplicates(subset=['category'])
    cur_user_unique.set_index('category', inplace=True)
    cur_user_unique = cur_user_unique.sort_values(by='category')
    cur_user_unique = cur_user_unique[cur_user_unique['gp_id'] == next_race_id]
    
    with open(f"{USER_GUESS_HISTORY_PATH}",'w') as f:
        f.write(f"### {'&nbsp;'*11} {user_name}'s guesses for {race_name} {datetime.datetime.now().year}\n")
        f.write(cur_user_unique['driver_name'].to_markdown())
    
    #! TEST if multiple users create histories, and all files have the same name -> conflict or time delay is enough

    cmd = f'pandoc {USER_GUESS_HISTORY_PATH} -o {USER_GUESS_HISTORY_PDF_PATH}.pdf'
    cmd2 = f'pdftoppm {USER_GUESS_HISTORY_PDF_PATH}.pdf {USER_GUESS_HISTORY_PDF_PATH} -png'
    cmd3 = f'convert {USER_GUESS_HISTORY_PDF_PATH}-1.png -crop 500x500+350+235 {USER_GUESS_HISTORY_PDF_PATH}_zoomed.png'
    os.system(cmd)
    os.system(cmd2)
    os.system(cmd3)

    await ctx.response.send_message(file=discord.File(f"{USER_GUESS_HISTORY_PDF_PATH}_zoomed.png"))

@bot.tree.command(name="mypoints",description="Show user's points in total")
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
    prev_race_id = f1_module.get_prev_gp_id()
    prev_race_name = f1_module.get_prev_gp_name()
    user_score = cur_user_db["round_score"][prev_race_id]["score_board"]
    user_score_df = f1_data.pd.DataFrame.from_dict(user_score,orient='index')
    user_score_df.rename(columns={0: 'Point'}, inplace=True)
    #logger.info(f"{user_name = } {prev_race_name = } {user_score_df = }")
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
    next_event_details = {r_t: datetime.datetime.strptime(time,'%Y-%m-%d %H:%M:%S.%f') for r_t,time in f1_module.next_gp_details["sessions"].items()}
    descr=""
    #descr = f"The bot is in **{BOT_STATE}** mode.\n"
    disp_minute = ""
    
    for r_t,time in next_event_details.items():
        if time.minute < 10:
            disp_minute = str(time.minute)+"0"
        else:
            disp_minute = str(time.minute)
        descr += f"{time.day} {calendar.month_abbr[int(time.month)]}, {time.hour}:{disp_minute} - {r_t}\n"
    location = f1_module.get_next_gp_name()
    embed=discord.Embed(colour=0xFFFFFF,title=f"Race Information\n{location}",description=descr)
    await ctx.response.send_message(embed=embed)

@bot.tree.command(name="hello",description="-")
async def hello(ctx:Interaction):
    await ctx.response.send_message(f"Hello there! {ctx.guild.default_role}")

@bot.tree.command(name="help",description="-")
async def embed_test(ctx:Interaction):
    descr = f"-------------------------------------------------------------------------------\n\
    First, take your guesses by **/guess**\n\
    Then wait until the grand prix completes\n\
    Finally evaluate your score by **/eval**\n\
    In the meanwhile,\n\
    you can see your guess by **/myguesses**\n\
    and you can see your point by **/mypoints**\n\
    And of course invoke many *funny* commands as well\n\
    \nGood luck! 😁🏁\n*the developer*"
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
    elif pia == "vodka":
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