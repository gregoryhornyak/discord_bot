# This example requires the 'members' and 'message_content' privileged intents to function, therefore using intents=discord.Intents.all()

#----< Imports >----#

import discord
from discord.ext import commands

import datetime
import os

from include.logging_manager import logger
from include.constants import *
from include.f1_data_fetcher import *
from include.database_manager import *

import asyncio
from dateutil.parser import parse


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
    upcoming_date = ""
    while True:
        channel = bot.get_channel(CHANNEL_ID)
        try:
            with open(f"{UPCOMING_DATE_PATH}upcoming_date", "r") as f:
                upcoming_date = f.readline()
                upcoming_date = parse(upcoming_date)
            logger.info(f"Date once set for: {upcoming_date}")
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
        if now.hour == 8 and now.minute == 5: # 8:05
            await channel.send("Doing daily routine",delete_after=3)
        if now.hour == 21 and now.minute == 42: # 8:05
            await channel.send("Doing daily routine")
        loop_counter += 1
        #logger.info(f"{loop_counter = }")
        await asyncio.sleep(50)

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
    await ctx.send("Bot is shutting down and will be upgraded...")
    await bot.close()

# function to get every racing date -> save to file -> update alert 

def get_discord_members(bot:commands.Bot):
    user_info = []
    for guild in bot.guilds:
        for member in guild.members:
            if member.name != "lord_maldonado":
                user_info.append({member.name: member.id})
    return user_info

@bot.command(aliases=["g","makeguess"])
async def guess(ctx):
    """Allows the user to make a guess"""
    await ctx.send("Fetching has begun... may take a while")

    # save the data into a file, to avoid long fetching
    drivers_info = get_drivers_info()
    #prev_race_id = get_prev_race_id_and_name()['id']
    #prev_race_name = get_prev_race_id_and_name()['name']
    next_race_id = get_next_race_id_and_name()['id']
    next_race_name = get_next_race_id_and_name()['name']

    select_race = discord.ui.Select(placeholder="Choose a race!",
                                    options=[discord.SelectOption(
                                        label=race_name, description="---") for race_name in F1_RACE_TYPES])
    select_driver = discord.ui.Select(placeholder="Choose a driver",
                                      options=[discord.SelectOption(
                                          label=driver,description=team) for driver,team in drivers_info.items()])
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
        
        save_guess(ctx,select_race,select_driver,next_race_id)
        await interaction.response.send_message("You have submitted your guess!")

    select_driver.callback = driver_callback
    select_race.callback = race_callback
    press_button.callback = button_callback
    message = f"Choose driver and race type\nfor {next_race_name} {datetime.datetime.now().year}\n**(use this form for multiple guesses)**"
    await ctx.send(message, view=theView)

schedule_2023 = "https://www.formula1.com/en/latest/article.formula-1-update-on-the-2023-calendar.4pTQzihtKTiegogmNX5XrP.html"

@bot.command()
async def calendar(ctx):
    schedule_2023_unknown = "https://www.autosport.com/f1/schedule/2023/"
    calendar_response = requests.get(schedule_2023_unknown).text
    calendar_soap = BeautifulSoup(calendar_response, 'html.parser')
    #logger.info(f"{calendar_soap = }")
    calendar_table = calendar_soap.find_all("tbody", class_="ms-schedule-table__item ms-schedule-table--local")
    logger.info(f"{calendar_table}")
    calendar_table_text = [name.get_text().strip() for name in calendar_table]
    logger.info(f"{calendar_table_text = }")
    calendar_table_text_clean = [name.split("\n") for name in calendar_table_text]
    logger.info(f"{calendar_table_text_clean = }")

@bot.command(aliases=["e","evaluate"])
async def eval(ctx):
    """read the results, and compare them with the guesses
    could only happen after the race"""

    # FETCHING

    # save dataframes into data/fetched_data every morning

    # headers: | Pos No Driver Car Laps Time/Retired PTS
    await ctx.send("Fetching has begun... may take a while")

    scores_json = f1_results_pipeline()
    logger.info(f"scores_json: {scores_json}")
    await ctx.send(scores_json,delete_after=3)

    #await ctx.send(file=discord.File(UPLOADS_PATH+"verstappen.mp3"))

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

    with open(f"{INVENTORY_PATH}guess_db.json", "r") as f:
        guess_db = json.load(f)
    # does it need to be transformed into a dataframe?
    guess_db = pd.DataFrame.from_dict(guess_db, orient='index')
    guess_db.reset_index(inplace=True)
    guess_db.rename(columns={'index': 'time_stamp'}, inplace=True)
    guess_db_reversed = guess_db.iloc[::-1]
    logger.info(f"{guess_db_reversed = }")

    # results - official results

    with open(f"{RESULTS_PATH}results.json", "r") as f:
        results = json.load(f)

    # collect score table entries

    with open(f'{SCORE_TABLE_PATH}score_table.json', 'r') as f:
        scoring_board = json.load(f)

    # users_db

    with open(f'{INVENTORY_PATH}users_db.json', 'r') as f:
        users_db = json.load(f)

    # f1 data

    f1_data_fetcher = F1DataFetcher()
    race_id = f1_data_fetcher.prev_race_id

    # collect users

    members = get_discord_members(bot)
    logger.info(f"{members = }")

    # --- all resources are collected

    ## ready for evaluation  

    # for every user
    for user_details in members:
        for user_name, user_id in user_details.items():
            user_guesses = guess_db_reversed[guess_db_reversed['user_name'] == user_name]
            user_guesses_unique = user_guesses.drop_duplicates(subset=['race_type'])
            # for every guess
            for (guessed_race_type, guessed_driver_name) in (zip(user_guesses_unique['race_type'], user_guesses_unique['driver_name'])):
                # for every race_type's result
                for race_type,driver_name in scores_json.items():
                    if guessed_race_type == race_type:
                        if guessed_driver_name == driver_name:
                            logger.info(f"{user_name}: match! {driver_name},{race_type}")
                            point = scoring_board[race_type] # each race_type's score
                            await ctx.send(f"{user_name} guessed correct: {driver_name} | {race_type} - {point} points!")
                            #if round_score not empty:
                            users_db[str(user_id)]["round_score"][str(race_id)]["score_board"][race_type] = driver_name # if not DNF
                            

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
    await ctx.send(file=discord.File(UPLOADS_PATH+"botlogs_extract_"+str(num_of_lines)+".pdf"),delete_after=6)

    """
    Error producing PDF.
    ! Undefined control sequence.
    l.277 {[}`Bahrain GP\n
    """

    # only send back last N number of lines to reduce file size

@bot.command(aliases=['myguess','mylast'])
async def myguesses(ctx):
    with open(f"{INVENTORY_PATH}guess_db.json", "r") as f:
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
    race_name = get_next_race_id_and_name()["name"]
    with open(f"{UPLOADS_PATH}user_guesses_list.md",'w') as f:
        f.write(f"### {'&nbsp;'*11} {ctx.author.name}'s guesses for {race_name} {datetime.datetime.now().year}\n")
        f.write(cur_user_unique['driver_name'].to_markdown())
    cmd = f'pandoc {UPLOADS_PATH}user_guesses_list.md -o {UPLOADS_PATH}user_guesses_list.pdf'
    cmd2 = f'pdftoppm {UPLOADS_PATH}user_guesses_list.pdf {UPLOADS_PATH}user_guesses_list -png'
    cmd3 = f'convert {UPLOADS_PATH}user_guesses_list-1.png -crop 500x500+350+235 {UPLOADS_PATH}user_guesses_list_zoomed.png'
    os.system(cmd)
    os.system(cmd2)
    os.system(cmd3)
    await ctx.send(file=discord.File(f"{UPLOADS_PATH}user_guesses_list_zoomed.png"))

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


#----< Main Function Init >----#


if __name__ == "__main__":
    pass