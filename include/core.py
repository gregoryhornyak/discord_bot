#----< Imports >----#

import datetime
import os
import typing
import asyncio
import subprocess
import calendar
from PIL import Image, ImageFont, ImageDraw
import random

import discord
from discord.ext import commands

from discord.interactions import Interaction
from dateutil.parser import parse

import include.f1_data_manager as f1_data
import include.database_manager as db_man

from include.logging_manager import logger
from include.constants import *

#----< Bot init >----#

bot = commands.Bot(command_prefix="/",intents=discord.Intents.all())

f1_module = f1_data.F1DataFetcher()

# new feature: in logs, show: time|user|command|success 

def get_channel_info(to_return="CHANNEL_ID"):
    """to_return = channel_id / server_id"""
    with open(f"{SERVER_CHANNEL_ID_PATH}","r") as f:
        discord_data = json.load(f)
    if to_return.lower() == "channel_id":
        return discord_data["CHANNEL_ID"]
    if to_return.lower() == "server_id":
        return discord_data["SERVER_ID"]

@bot.event
async def on_ready():
    logger.info(f'Logging in as {bot.user}')
    # synchronise commands globally
    server_id = get_channel_info("SERVER_ID")
    channel_id = get_channel_info("CHANNEL_ID")
    bot.tree.copy_global_to(guild=discord.Object(id=server_id))
    await bot.tree.sync(guild=discord.Object(id=server_id))
    channel = bot.get_channel(channel_id)
    
    await channel.send("Bot started",silent=True)

    await bot.change_presence(activity=discord.Game(name=f"in {BOT_STATE} mode"))

    #await channel.last_message.edit(content=BOT_START_SHORT_MESSAGE)

    # start agents
    await notification_agent()
    #await guess_agent()

"""
@bot.event
async def on_message(ctx:Interaction):
    if ctx.author.name != "lord_maldonado":
        # search any swear words in the messages
        did_swear = [item for item in SWEAR_WORDS if item in ctx.content.lower()]
        if did_swear:
            await ctx.channel.send(random.choice(BLACK_LISTED_PHRASES))
"""

async def notification_agent():
    with open(f"{SERVER_CHANNEL_ID_PATH}","r") as f:
        discord_data = json.load(f)
    loop_counter = 0
    while True:
        channel = bot.get_channel(discord_data["CHANNEL_ID"])
        now = datetime.datetime.now()

        # do daily fetch
        if now.hour == 4 and now.minute == 20:
            f1_module.daily_fetch()
            pass

        next_grand_prix_events_time = {category: datetime.datetime.strptime(time,LONG_DATE_FORMAT) for category,time in f1_module.next_gp_details["sessions"].items()}  
        delta = now.replace(second=0, microsecond=0) + datetime.timedelta(days = 1)
        delta_3_days = now.replace(second=0, microsecond=0) + datetime.timedelta(days = 3)
        for r_t, time in next_grand_prix_events_time.items():
            # 2024-02-29 11:30:00.000000
            if time.month == delta.month and time.day == delta.day and time.hour == delta.hour and time.minute == delta.minute:
                await channel.send(f"{r_t} starts in 1 day!") # seems oke
            # for 2,1 hours and over, time has been shifted 1 hour earlier due to time issues
            if now.month == time.month and now.day == time.day and now.hour+2 == time.hour-1 and now.minute == time.minute:
                if r_t == "race":
                    await channel.send(f"{r_t} starts in 2 hours!") 
                    
            if now.month == time.month and now.day == time.day and now.hour+1 == time.hour-1 and now.minute == time.minute:
                if r_t == "race":
                    await channel.send(f"{channel.guild.default_role} {r_t} starts in **1 hour**! Take your guesses!")
                    
            if now.month == time.month and now.day == time.day and now.hour == time.hour-1 and now.minute == time.minute:
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
    """user_id: user_name"""
    user_info = {}
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            user_info[str(member.id)] = member.name
    # if csokker not in db
    user_info["69420"] = "csokker99"
    return user_info

async def save_discord_members_pics(ctx:Interaction) -> list: # dont change it
    for member in ctx.guild.members:
        if member.name != "lord_maldonado":
            try:
                await member.avatar.save(f"{PROFILE_PICS_PATH}{member.name}.png")
            except AttributeError:
                await member.default_avatar.save(f"{PROFILE_PICS_PATH}{member.name}.png")

@bot.tree.command(name="guess",description="Make a guess for a category and a driver")
async def guess(ctx:discord.Interaction): #include DNF
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
    select_dnf = discord.ui.Select(placeholder="Choose number of DNF",
                                   options=[discord.SelectOption(label=str(number)) for number in range(0,21)])
    
    press_button = discord.ui.Button(label="SUBMIT",style=discord.ButtonStyle.primary)
    press_dnf_button = discord.ui.Button(label="SUBMIT DNF",style=discord.ButtonStyle.secondary)
    theView = discord.ui.View()
    theView.add_item(select_race)
    theView.add_item(select_driver)
    theView.add_item(select_dnf)
    theView.add_item(press_button)
    theView.add_item(press_dnf_button)
    
    async def driver_callback(sub_interaction:Interaction):
        await sub_interaction.response.defer()

    async def race_callback(sub_interaction:Interaction):
        await sub_interaction.response.defer()
        
    async def dnf_callback(sub_interaction:Interaction):
        await sub_interaction.response.defer()

    async def dnf_button_callback(sub_interaction:Interaction):
        name = sub_interaction.user.name
        id = sub_interaction.user.id
        logger.debug(f"{select_dnf.values = }")
        try:
            logger.info(f"{name}: {select_dnf.values[0]}: {next_race_name.capitalize()}")
        except (IndexError, NameError, AttributeError) as e:
            logger.error("No DNF selected")
        else:
            next_gp_id = f1_module.next_gp_details['id']
            #next_gp_name = f1_module.next_gp_details['name']
            count = select_dnf.values[0]
            db_man.save_guess(name=name,id=id,select_race="R_DNF",select_driver=count,dnf=True,next_race_id=next_gp_id)
            await sub_interaction.response.send_message(f"<{name}: R_DNF: {select_dnf.values[0]}: {next_race_name.capitalize()}>",silent=True)

    async def button_callback(sub_interaction:Interaction):
        name = sub_interaction.user.name
        id = sub_interaction.user.id
        logger.debug(f"{select_race.values = }")
        try:
            logger.info(f"{name}: {select_race.values[0]}: {select_driver.values[0]}: {next_race_name.capitalize()}")
        except (IndexError, NameError, AttributeError) as e:
            logger.error("No driver or/and category selected")
        else:
            await sub_interaction.response.send_message(f"<{name}: {select_race.values[0]}: {select_driver.values[0]}: {next_race_name.capitalize()}>",silent=True)
        
        
        #logger.info(f"{name}: {select_race.values[0]}: {select_driver.values[0]}: {next_race_name.capitalize()}")
        db_man.save_guess(name=name,
                          id=id,
                          select_race=select_race.values[0],
                          select_driver=select_driver.values[0],
                          next_race_id=next_race_id) # dnf=False
        # check if already guessed this
        #await sub_interaction.response.send_message(f"Nothing happened",silent=True)

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    select_dnf.callback = dnf_callback
    press_button.callback = button_callback
    press_dnf_button.callback = dnf_button_callback

    message = f"Guess for {next_race_name} {datetime.datetime.now().year}\n**(use this form for multiple guesses)**"
    await ctx.followup.send(content=message, view=theView)
    #await ctx.edit_original_response()

def get_complete_database() -> f1_data.pd.DataFrame:
    
    # SCORE-TABLE 
    score_board = {}
    try:
        with open(f'{SCORE_TABLE_PATH}', 'r') as f:
            score_board = json.load(f)
    except Exception as e:
        logger.error(e)
    score_board_df = f1_data.pd.DataFrame.from_dict(score_board, orient='index')
    score_board_df.reset_index(inplace=True)
    score_board_df.rename(columns={'index': CATEGORY}, inplace=True)
    score_board_df.rename(columns={0: SCORE}, inplace=True)
        
    # guess database
    guess_database = {}
    with open(f"{GUESS_DB_PATH}", "r") as f:
        guess_database = json.load(f)
    guess_db = f1_data.pd.DataFrame.from_dict(guess_database, orient='index')
    guess_db.reset_index(inplace=True)
    guess_db.rename(columns={'index': TIME_STAMP}, inplace=True)
    guess_db_df = guess_db.iloc[::-1]
    
    # dict of previous GP results
    
    all_gp_results = f1_module.get_all_prev_gps_details()
    all_gp_results_df = f1_data.pd.DataFrame(columns=[GP_ID,GP_NAME,CATEGORY,RESULT])
    for gp_id, gp_info in all_gp_results.items():
        for category,outcome in gp_info[RESULT].items():
            all_gp_results_df.loc[len(all_gp_results_df)] = {GP_ID:gp_id, GP_NAME:gp_info[GP_NAME], CATEGORY:category, RESULT:outcome}
    
    users_db_df = f1_data.pd.DataFrame(columns=[GP_ID,GP_NAME,CATEGORY,RESULT])
    for gp_id, gp_info in all_gp_results.items():
        for category,result in gp_info[RESULT].items():
            users_db_df.loc[len(users_db_df)] = {GP_ID:gp_id, GP_NAME:gp_info[GP_NAME], CATEGORY:category, RESULT:result}
    
    name_guess_result_df = f1_data.pd.DataFrame.merge(guess_db_df, users_db_df, on=[GP_ID,CATEGORY], how='inner')
    name_guess_result_df = name_guess_result_df.sort_values(by=[USERNAME,TIME_STAMP])
    name_guess_result_df = name_guess_result_df.iloc[::-1] # reverse dataframe -> latest first
    # since latest first, uniques will be marked by first occurance -> rest deleted
    name_guess_result_df = name_guess_result_df.groupby([USERNAME,GP_ID]).apply(lambda x: x.drop_duplicates(CATEGORY)).reset_index(drop=True)
    # assign points to categories
    name_guess_result_point_df = f1_data.pd.DataFrame.merge(name_guess_result_df, score_board_df, on=CATEGORY, how='left')
    # take away points if wrong guess
    name_guess_result_point_df.loc[name_guess_result_point_df[DRIVER_NAME] != name_guess_result_point_df[RESULT], SCORE] = 0
    return name_guess_result_point_df

@bot.tree.command(name="evaluate",description="-")
async def eval(ctx:discord.Interaction):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    # need some time
    await ctx.response.defer()

    # EVALUATING

    # 1. find all the users who guessed (if didnt, out of game)
    # 2. if more guesses under same category then latest matters.
    # 3. if didnt guess in a category then doesn't get points
    # 4. assign score board value

    #
    # IMPORTANT: DNF IS STRING USING DRIVER_NAME KEY -> too much fuss in the for cycle
    #
    
    complete_df = get_complete_database()
    complete_df = complete_df[complete_df[GP_ID].isin(f1_module.get_all_prev_gp_id())]
    participants = get_discord_members(ctx)
    
    #todo convert this dictionary-transform into a dataframe -> dict using built-in Pandas methods
    local_dict = {}
    for user_id in complete_df[USER_ID].unique():
        cur_user_db = complete_df[complete_df[USER_ID]==user_id]
        local_dict[user_id] = {
            USERNAME: participants[user_id],
            "grand_prix": {},
            "session_score": 0
        }
        for gp in cur_user_db[GP_ID].unique():
            cur_user_cur_gp_db = cur_user_db[cur_user_db[GP_ID]==gp]
            cat_sco_table = f1_data.pd.Series(cur_user_cur_gp_db[SCORE].values,index=cur_user_cur_gp_db[CATEGORY]).to_dict()
            local_dict[user_id]["grand_prix"][gp] = {key: int(value) for key, value in cat_sco_table.items()}
            local_dict[user_id]["grand_prix"][gp]["grand_prix_score"] = int(cur_user_cur_gp_db[SCORE].values.sum())
            local_dict[user_id]["grand_prix"][gp]["podium_score"] = 0
            table = local_dict[user_id]["grand_prix"][gp]
            try:
                if table["R1"] !=0 and table["R2"] !=0 and table["R3"] !=0:
                    local_dict[user_id]["grand_prix"][gp]["podium_score"] = 1
            except KeyError:
                logger.info(f"{user_id} - no podium")
        for gp_id in local_dict[user_id]["grand_prix"].keys():
            local_dict[user_id]["session_score"] += local_dict[user_id]["grand_prix"][gp_id]["grand_prix_score"]
        local_dict[user_id]["session_score"] += local_dict[user_id]["grand_prix"][gp]["podium_score"]


    logger.info("Evaluation completed")
    
    # create leaderboard
    scores = {user_info[USERNAME]:user_info["session_score"] for user_info in local_dict.values()}
    unique_scores = {value for value in scores.values()}
    
    descr = ""
    winners = []
    for u_s in unique_scores:
        descr += f"{u_s} pts: "
        same_score_users = [key for key, val in scores.items() if val == u_s]
        winners = same_score_users
        for uname in same_score_users:
            descr += f"{uname}  "
        descr += "\n"
    descr += f"\n**Congrats to {'  '.join(winners)}**\n"

    
    logger.debug(f"{descr = }")
    embed=discord.Embed(colour=0xFFFFFF,title=f"Season leaderboard",description=descr)
    await ctx.followup.send(embed=embed)
    try:
        if local_dict:
            with open(f'{USERS_DB_PATH}', 'w') as f:
                json.dump(local_dict,f,indent=4)
    except TypeError:
        logger.debug("INT64 error")

@bot.tree.command(name="force_fetch",description="ADMIN - Fetch latest info right now")
async def force_fetch(ctx:discord.Interaction,password:str):    
    with open(f"{PASSW_PATH}",'r') as f:
        found_pw = f.read().strip()
        logger.info(f"{password}!={found_pw} is {password!=found_pw}")
        if password!=found_pw:
            await ctx.response.send_message("Wrong password")
            return 0
    f1_module.fetch_menu(forced=True)
    logger.info("F1 modules fetched up-to-date info")
    await ctx.response.send_message("Force fetching completed",ephemeral=True)

#--------< Additional Functions >----#

@bot.tree.command(name="rules",description="-")
async def rules(interaction:Interaction):
    rule_book = """
Rules for guessing:
1. find all the users who guessed (if didnt, out of game).
2. if more guesses under same category, then latest matters.
3. if didnt guess in a category, then doesn't get points.
"""
    await interaction.response.send_message(rule_book)

@bot.tree.command(name="get_logs",description="ADMIN - show logs ")
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
    cmd = f'pandoc {BOT_LOGS_EXT_MD_PATH} -o {BOT_LOGS_EXT_PDF_PATH}'
    os.system(cmd)    
    logger.info(f'sending {BOT_LOGS_EXT_PDF_PATH+"_"+str(num_of_lines)+".pdf"}')
    await ctx.response.send_message(file=discord.File(BOT_LOGS_EXT_PDF_PATH),delete_after=6)

    # only send back last N number of lines to reduce file size

@bot.tree.command(name="my_guesses",description="Show user's guesses for next grand prix")
async def myguess(ctx:discord.Interaction,username:str=""):
    with open(f"{GUESS_DB_PATH}", "r") as f:
            guesses_database = json.load(f)
    user_guesses = f1_data.pd.DataFrame.from_dict(guesses_database, orient='index')
    user_guesses.reset_index(inplace=True)
    user_guesses.rename(columns={'index': 'time_stamp'}, inplace=True)
    user_guesses_reversed = user_guesses.iloc[::-1]
    #user_name = ctx.user.name
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
    logger.info("markdown to pdf")
    os.system(cmd2)
    logger.info("pdf to png")
    os.system(cmd3)
    logger.info("cropped png")

    await ctx.response.send_message(file=discord.File(f"{USER_GUESS_HISTORY_PDF_PATH}_zoomed.png"),ephemeral=True)

@bot.tree.command(name="generate_report",description="Complete report on results")
async def generate_report(ctx:discord.Interaction):
    """name | guess | result | point"""

    complete_df= get_complete_database()
    logger.debug(f"{ctx.user.id = }")
    logger.debug(f"{complete_df[complete_df[USER_ID] == str(ctx.user.id)] = }")
    try:
        complete_df = complete_df[complete_df[USER_ID] == str(ctx.user.id)]
    except Exception as e:
        logger.error(e)
    complete_df = complete_df.drop(columns=[TIME_STAMP,USER_ID,GP_ID,DRIVER_NAME])
    
    with open(f"{REPORT_PATH}",'w') as f:
        f.write(complete_df.to_markdown(index=False))
    
    #! TEST if multiple users create histories, and all files have the same name -> conflict or time delay is enough

    cmd = f'pandoc {REPORT_PATH} -o {REPORT_PDF_PATH}.pdf'
    
    os.system(cmd)
    logger.info("markdown to pdf")
    await ctx.response.send_message(file=discord.File(f"{REPORT_PDF_PATH}.pdf"),ephemeral=True)
    
#--------< Funny Functions aka Easter Eggs >----#

@bot.tree.command(name="dadjoke",description="-")
async def dadjoke(ctx:Interaction):
    cmd = 'curl -H "Accept: application/json" https://icanhazdadjoke.com/'
    output = subprocess.check_output(cmd, shell=True,text=True)
    joke_json = json.loads(output)
    await ctx.response.send_message(f'Dad joke of the day:\n{joke_json["joke"]}',ephemeral=True)

@bot.tree.command(name="who_am_i",description="-")
async def whoami(ctx:Interaction):
    await ctx.response.send_message(f"You are {ctx.user.name},\nHey <@{ctx.user.id}>",ephemeral=True)

@bot.tree.command(name="info",description="-")
async def info(ctx:Interaction):
    # export this dict compr to F1_module as func
    next_event_details = {r_t: datetime.datetime.strptime(time,LONG_DATE_FORMAT) for r_t,time in f1_module.next_gp_details["sessions"].items()}
    descr=""
    disp_minute = ""
    
    for r_t,time in next_event_details.items():
        if time.minute < 10:
            disp_minute = str(time.minute)+"0"
        else:
            disp_minute = str(time.minute)
        descr += f"{time.day} {calendar.month_abbr[int(time.month)]}, {time.hour}:{disp_minute} - {r_t}\n"
    descr+=f"\nLOCAL TIME: {datetime.datetime.now()}\n"
    location = f1_module.get_next_gp_name()
    embed=discord.Embed(colour=0xFFFFFF,title=f"Race Information\n{location}",description=descr)
    await ctx.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="hello",description="-")
async def hello(ctx:Interaction):
    await ctx.response.send_message(f"Hello there! {ctx.guild.default_role}",ephemeral=True)

@bot.tree.command(name="help",description="-")
async def embed_test(ctx:Interaction):
    descr = f"First, take your guesses by **/guess**\n\
Then wait until the grand prix completes\n\
Finally evaluate your score by **/evaluate**\n\
In the meanwhile,\n\
you can see your guess by **/my_guesses**\n\
or you can request a report with **/generate_report**\n\
And of course invoke many *funny* commands as well\n\
    \nGood luck! 😁🏁\n*the developer*"
    embed=discord.Embed(title="Tutorial",
                        description=descr,
                        color=0xFF5733)
    await ctx.response.send_message(embed=embed,ephemeral=True)

@bot.tree.command(name="pina",description="fúú, te kibaszott perverz")
async def pina(ctx:Interaction):
    await ctx.response.send_message("Itt egy titkos pina csak neked: || () ||",ephemeral=True)

@bot.tree.command(name="fasz",description="fúú, te kibaszott perverz")
async def fasz(ctx:Interaction):
    await ctx.response.send_message("Itt egy titkos fasz csak neked: || 8===Đ ||",ephemeral=True)

@bot.tree.command(name="jo_isten_kuldte_hozzank_le",description="-")
async def vitya(ctx:Interaction):
    await ctx.response.send_message(file=discord.File(UPLOADS_PATH+"vitya.png"),ephemeral=True)

@bot.tree.command(name="kozso",description="-")
async def kozso(ctx:Interaction):
    kozso_lines = ["A delfinek.. a víz alatt.. nagyon jó emberek!","Az éérzéések, a szerelem, az ébredések, a kaják, a vizek, a min-mindent imádok, miindent pozitiven csak!"]
    await ctx.response.send_message(random.choice(kozso_lines),ephemeral=True)

@bot.tree.command(name="ki_az_az_alekosz",description="mindjart megtudod")
async def alekos(ctx:Interaction):
    logger.info("alekosz kitálal")
    script = f"""**NÉV:** Nagy Alekosz
**ATTRIBUTUMOK:**
Nemzetközi sztár
Vagyonőr
Taxisofőr
Üzletember 
Etikus hacker 
Előadóművész
Értelmiségi 
Gróf 
Korona herceg 
Civil politikai elemző
Testépítő 
Író 
BRFK által megfigyelt, lehallgatott, követett személy 
Nemzetbiztonsági kockázat
Tényező 
Állandó stratégiai gócpont
A Karinthy gyűrű várományosa
Istencsapás
Csendestárs
Donor
Fajvédelmi operatív 
Békaember
Régi új fideszes  
Macséte 
Kozmológus
Kriminológus 
Túravezető 
Gurmé 
Munkásőr
Férfi szex szimbólum 
Világbajnok
Tavi finánc 
Direktor 
Kényszerszexuális
Klíma tulajdonos 
Színész 
A magyar csillag
Kolosszus 
Privát rendszám tulajdonos  
Seuso-kincs tulajdonos"""

    embed=discord.Embed(title="Nagy Alekosz",
                        description=script,
                        color=0xFF5733)
    await ctx.response.send_message(embed=embed,ephemeral=True)

### UNSTABLE
"""
@bot.tree.command(name="gyere",description="-")
async def join(ctx:Interaction):
    await ctx.response.defer()
    if ctx.guild.voice_client is not None:
        return await ctx.guild.voice_client.move_to("General")
    channel = [chnl for chnl in ctx.guild.voice_channels][0]
    await channel.connect()

@bot.tree.command(name="halljuk",description="-")
async def play(ctx:Interaction, person:typing.Literal["lajos","hosszulajos","vitya","max","feri","hektor","kozso","furaferi"]):
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
    await ctx.guild.voice_client.disconnect()
    #await ctx.followup.send("---",ephemeral=True)
"""

