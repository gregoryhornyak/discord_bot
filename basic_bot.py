# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands
import random
import asyncio
import f1_schedule
import db_manager

description = '''An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', description=description, intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('------')


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
    print("img request")
    await ctx.send(file=discord.File('my_image.jpeg'))
    print("sent image")

@bot.command()
async def guess(ctx,event,guess):
    # prepare arguments
    present = f1_schedule.get_present(as_str=True)
    user = ctx.author.name
    # store input
    db_manager.append_db('db1.json',present,user,event,guess)
    # reply
    await ctx.send(f'Your guess {guess} for {event} has been saved.')

@bot.command()
async def showlast(ctx):
    present = f1_schedule.get_present(as_str=True)
    user = ctx.author.name
    date,latest = db_manager.last_entry('db1.json',user,present)
    await ctx.send(f'Your last guess was:\n{date}:\n{latest}')

@bot.command()
async def next(ctx):
    session_dates = f1_schedule.get_future_sessions()
    await ctx.send('Lemme find it...')
    await ctx.send(f'The next event is on {session_dates[0]}')

@bot.command()
async def dako(ctx, length):
    mid = "="
    mid += "="*int(length)
    if int(length) < 41:
        await ctx.send(f"itt egy meretes fasz csak neked:\n8{mid}D")
    else:
        await ctx.send(f'ekkora dakoval hogy tudsz te létezni?')

@bot.command()
async def whoami(ctx):
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
    await ctx.send("""To guess a score: SIGN+guess -> SCORE
To see every guess: SIGN+board
To only see your guesses: SIGN+myboard""")

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')

@bot.command()
async def lajos(ctx):
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
-Szia"""
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

TOKEN = 'MTA3ODQyNTM4ODE4ODk3NTEwNA.GLbQLC.ifxTnJ5KUuL912FEIEZHNq8N_JdnvGkG7Ilbj0'

bot.run(TOKEN)

print(f'Bot has been terminated')

#@bot.event
#async def on_end

"""
Timestamp + Author - auto
make a guess:
!TIPP EVENT GUESS[STRING/BOOL]

!SHOWLAST -
# show everyone's last guesses and total_points

---------------------------
API request | RapidAPI

filter by criteria

save values/scores

match name with guess_name

hand out given amount of point to user

DB1:
name - point - per event - total_points(seasonal)

DB2:
input logs:
timestamp - author - event - guess

DB3: optional
results

Race schedule: GMT +0

------

At one time: guess for all types



"""
