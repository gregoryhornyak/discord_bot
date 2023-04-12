# This example requires the 'members' and 'message_content' privileged intents to function.

import discord
from discord.ext import commands
import random
import asyncio
import datetime
import sys
import inspect
sys.path.append('../src')
from include import f1_schedule
from include import db_manager
from include import logging_machine

description = '''An example bot to showcase the discord.ext.commands extension module.
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
    local_log = logging_machine.createLog(str(datetime.datetime.now()), 
                                          'input', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name,
                                          data=f"event: {event}\n\tguess: {guess}")
    # prepare arguments
    present = f1_schedule.get_present(as_str=True)
    user = ctx.author.name
    # store input
    db_manager.append_db('db1.json',present,user,event,guess)
    # reply
    await ctx.send(f'Your guess {guess} for {event} has been saved.')

@bot.command()
async def note(ctx,*notes):
    print(f"notes: {notes}")

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
    local_log = logging_machine.createLog(str(datetime.datetime.now()), 
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
    local_log = logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name)
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
    local_log = logging_machine.createLog(str(datetime.datetime.now()), 
                                          'output', 
                                          inspect.currentframe().f_code.co_name,
                                          ctx.author.name)
    await ctx.send("""To guess a score: SIGN+guess -> SCORE
To see every guess: SIGN+board
To only see your guesses: SIGN+myboard""")

@bot.command()
async def joined(ctx, member: discord.Member):
    """Says when a member joined."""
    await ctx.send(f'{member.name} joined {discord.utils.format_dt(member.joined_at)}')

@bot.command()
async def lajos(ctx):
    local_log = logging_machine.createLog(str(datetime.datetime.now()), 
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
-Szia"""
    for line in script.split('\n'):
        await ctx.send(line)

@bot.command()
async def szeretsz_elni(ctx):
    local_log = logging_machine.createLog(str(datetime.datetime.now()), 
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

def main():

    print(f'{sys.argv[0] = }')
    print(f'{sys.argv[1] = }')

    TOKEN = sys.argv[1]

    bot.run(TOKEN)

    print(f'Bot has been terminated')

if __name__ == "__main__":
    main()