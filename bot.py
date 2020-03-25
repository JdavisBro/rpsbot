import discord
from discord.ext import commands
import asyncio,logging,json,os,random,datetime

TOKEN = "TOKEN"
hostname = "http://127.0.0.1:8080/html/" # Hostname - Used for links to page - include a / at the end
defaultTime = 600 # default time for when a guild adds a channel (seconds)

logging.basicConfig(level=logging.INFO)
game = discord.Game("Starting Up!")
bot = commands.Bot(command_prefix="r!",description="Rock Paper Scissors!",activity=game)
channelsWrite = {}
scoresWrite = {}
ongoingGames = {}

if os.path.exists("channels.json"):
    logging.info("channels.json already exists!")
else:
    try:
        open("channels.json","x")
        open("channels.json","w+").write("{}")
        logging.info("channels.json created!")
    except:
        logging.info("There was an error creating channels.json.")
        raise

if os.path.exists("html"):
    logging.info("html directory already exists!")
else:
    try:
        os.mkdir("html")
        logging.info("html directory created!")
    except:
        logging.info("There was an error creating the html directory.")
        raise
if os.path.exists("html/scores.json"):
    logging.info("html/scores.json already exists!")
else:
    try:
        open("html/scores.json","x")
        open("html/scores.json","w+").write("{}")
        logging.info("html/scores.json created!")
    except:
        logging.info("There was an error creating html/scores.json.")
        raise

async def write_dictionary():
    while True:
        if channelsWrite:
            with open("channels.json","r+") as f:
                channelsDict = json.load(f)
            for id in list(channelsWrite.keys()):
                channelsDict[id] = channelsWrite[id]
                if channelsWrite[id]["channel"] == "":
                    channelsDict.pop(id)
                channelsWrite.pop(id)
            with open("channels.json","w+") as f:
                json.dump(channelsDict,f,indent=4)
        if scoresWrite:
            with open("html/scores.json","r+") as f:
                scoresDict = json.load(f)
            for id in list(scoresWrite.keys()):
                scoresDict[id] = scoresWrite[id]
                scoresWrite.pop(id)
            with open("html/scores.json","w+") as f:
                json.dump(scoresDict,f,indent=4)
        await asyncio.sleep(1)

bot.loop.create_task(write_dictionary())

async def get_channels_dict():
    with open("channels.json","r+") as f:
        return json.load(f)

async def get_scores_dict():
    with open("html/scores.json","r+") as f:
        return json.load(f)

async def startup_check():
    channelsDict = await get_channels_dict()
    for guildid in channelsDict.keys():
        bot.loop.create_task(create_rps(guildid))

async def create_rps(guildid:str):
    channelDict = await get_channels_dict()
    if guildid not in channelDict.keys():
        await asyncio.sleep(2)
        channelDict = await get_channels_dict()
    channelDict = channelDict[guildid]
    channel = bot.get_channel(int(channelDict["channel"]))
    time = channelDict["time"]
    endtime = datetime.datetime.now() + datetime.timedelta(seconds=time)
    embed = discord.Embed(title="ROCK, PAPER, SCISSORS...   React with your choice!", colour=discord.Colour.from_rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255)),timestamp=endtime, description=f"[Click here for this server's scoreboard]({hostname + '?' + guildid})")
    embed.set_footer(text="This game will end at ")
    message = await channel.send(embed=embed)
    await message.add_reaction("🗿")
    await message.add_reaction("🧻")
    await message.add_reaction("✂️")
    ongoingGames[guildid] = {"message": message,"endtime": endtime}

async def check_for_endings():
    while True:
        if ongoingGames:
            for guildid in list(ongoingGames.keys()):
                if datetime.datetime.now() >= ongoingGames[guildid]["endtime"]:
                    bot.loop.create_task(end_game(guildid))
        await asyncio.sleep(5)

bot.loop.create_task(check_for_endings())

async def end_game(guildid):
    message = await ongoingGames[guildid]["message"].channel.fetch_message(ongoingGames[guildid]["message"].id)
    endtime = ongoingGames[guildid]["endtime"]
    ongoingGames.pop(guildid)
    reactions = message.reactions
    rockUsers = []
    paperUsers = []
    scissorsUsers = []
    for reaction in reactions:
        for user in await reaction.users().flatten():
            if user != message.guild.me:
                if reaction.emoji == "🗿":
                    rockUsers.append(user)
                elif reaction.emoji == "🧻":
                    paperUsers.append(user)
                elif reaction.emoji == "✂️":
                    scissorsUsers.append(user)
    await message.clear_reactions()
    choices = ["rock","paper","scissors"]
    choiceNames = {"rock": "🗿  ROCK","paper": "🧻  PAPER","scissors":"✂️ SCISSORS"}
    choice = random.choice(choices)
    embed = discord.Embed(title=f"ROCK, PAPER, SCISSORS... SHOOT! - I chose {choiceNames[choice]}", colour=discord.Colour.from_rgb(random.randint(0,255),random.randint(0,255),random.randint(0,255)), description=f"[Click here for this server's scoreboard]({hostname + '?' + guildid})", timestamp=endtime)
    embed.set_footer(text="Ended at ")
    winLoseDraw = "Draw" if choice == "rock" else "Win" if choice == "scissors" else "Lose"
    embed.add_field(name=f"🗿  ROCK - {winLoseDraw}", value='\n'.join([user.name for user in rockUsers]) + ".", inline=True)
    winLoseDraw = "Draw" if choice == "paper" else "Win" if choice == "rock" else "Lose"
    embed.add_field(name=f"🧻  PAPER - {winLoseDraw}", value='\n'.join([user.name for user in paperUsers]) + ".", inline=True)
    winLoseDraw = "Draw" if choice == "scissors" else "Win" if choice == "paper" else "Lose"
    embed.add_field(name=f"✂️ SCISSORS - {winLoseDraw}", value='\n'.join([user.name for user in scissorsUsers]) + ".", inline=True)
    await message.edit(embed=embed)
    rockPoints = 0 if choice == "rock" else 1 if choice == "scissors" else -1
    paperPoints = 0 if choice == "paper" else 1 if choice == "rock" else -1
    scissorsPoints = 0 if choice == "scissors" else 1 if choice == "paper" else -1
    scoresDict = await get_scores_dict()
    if guildid not in scoresDict.keys():
        scoresDict[guildid] = {}
    for user in rockUsers:
        userid = str(user.id)
        if userid not in scoresDict[guildid].keys():
            previousScore = 0
        else:
            previousScore = scoresDict[guildid][userid]["score"]
        scoresDict[guildid][userid] = {"name": user.name,"score": int(previousScore) + rockPoints}
    for user in paperUsers:
        userid = str(user.id)
        if userid not in scoresDict[guildid].keys():
            previousScore = 0
        else:
            previousScore = scoresDict[guildid][userid]["score"]
        scoresDict[guildid][userid] = {"name": user.name,"score": int(previousScore) + paperPoints}
    for user in scissorsUsers:
        userid = str(user.id)
        if userid not in scoresDict[guildid].keys():
            previousScore = 0
        else:
            previousScore = scoresDict[guildid][userid]["score"]
        scoresDict[guildid][userid] = {"name": str(user),"score": int(previousScore) + scissorsPoints}
    scoresWrite[guildid] = scoresDict[guildid]
    await asyncio.sleep(int((await get_channels_dict())[guildid]["betweenTime"]))
    if guildid in await get_channels_dict():
        bot.loop.create_task(create_rps(guildid))

@bot.event
async def on_reaction_add(reaction,user):
    if ongoingGames:
        for guildid in ongoingGames.keys():
            if ongoingGames[guildid]["message"].id == reaction.message.id:
                if (user == reaction.message.guild.me) or (reaction.emoji not in ["🗿","🧻","✂️"]):
                    return
                for otherReaction in reaction.message.reactions:
                    if (isinstance(otherReaction.emoji,str)) and (otherReaction.emoji in ["🗿","🧻","✂️"]) and (otherReaction != reaction) and (user in await otherReaction.users().flatten()):
                        await otherReaction.remove(user)
                break

@bot.command()
async def run(ctx,*,code):
    exec(code)
    await ctx.message.add_reaction("✅")

@bot.event
async def on_ready():
    game = discord.Game("Rock Paper Scissors")
    await bot.change_presence(activity=game)
    logging.info("BOT IS UP")
    bot.loop.create_task(startup_check())

@commands.has_permissions(manage_roles=True)
@bot.group(name="set")
async def cmd_set(ctx):
    if not ctx.invoked_subcommand:
        await ctx.send_help(ctx.command)

@cmd_set.command(name="channel")
async def cmd_set_channel(ctx,channel:discord.TextChannel=None):
    guildid = str(ctx.guild.id)
    if channel == None:
        channelsWrite[guildid]
    channelid = str(channel.id)
    channelsDict = await get_channels_dict()
    perms = channel.permissions_for(ctx.guild.me)
    if not perms.read_messages and not perms.send_message and not perms.manage_messages and not perms.embed_links:
        await ctx.send("I am missing at least one of the following permissions in that channel:\n```- Read Messages\n- Send Messages\n- Manage Messages\n- Embed Links")
        return
    if guildid not in channelsDict.keys():
        channelsDict[guildid] = {"channel": "","time": defaultTime}
    if channelsDict[guildid]["channel"] == channelid:
        await ctx.send("This server's channel is already that!")
        bot.loop.create_task(create_rps(guildid))
        return
    channelsDict[guildid]["channel"] = channelid
    channelsWrite[guildid] = channelsDict[guildid]
    await ctx.send(f"Rock Paper Scissors channel has been set to {channel.name}")
    bot.loop.create_task(create_rps(guildid))

@cmd_set.command(name="timeLast")
async def cmd_set_time(ctx,time:str=None):
    guildid = str(ctx.guild.id)
    if time == None:
        time = defaultTime
    channelsDict = await get_channels_dict()
    if guildid not in channelsDict.keys():
        await ctx.send("Set a channel first! `r!set channel (CHANNEL)`")
        return
    if time.endswith("m"):
        time = int(time[:-1]) * 60
    elif time.endswith("h"):
        time = int(time[:-1]) * 3600
    if int(time) < 30:
        await ctx.send("Time must be above 30 seconds")
        return
    if int(time) > 7200:
        await ctx.send("Time must be 2 hours or below (7200s)")
    if channelsDict[guildid]["time"] == time:
        await ctx.send("This server's channel is already that!")
        return
    channelsDict[guildid]["time"] = time
    channelsWrite[guildid] = channelsDict[guildid]
    await ctx.send(f"Rock Paper Scissors game time has been set to {time} seconds!")

@cmd_set.command(name="timeBetween")
async def cmd_set_time_between(ctx,time:str=None):
    guildid = str(ctx.guild.id)
    if time == None:
        time = defaultTime
    channelsDict = await get_channels_dict()
    if guildid not in channelsDict.keys():
        await ctx.send("Set a channel first! `r!set channel (CHANNEL)`")
        return
    if time.endswith("m"):
        time = int(time[:-1]) * 60
    elif time.endswith("h"):
        time = int(time[:-1]) * 3600
    if int(time) < 15:
        await ctx.send("Time must be above or 15 seconds")
        return
    if int(time) > 600:
        await ctx.send("Time must be 10 minutes or below (600s)")
    if channelsDict[guildid]["betweenTime"] == time:
        await ctx.send("This server's channel is already that!")
        return
    channelsDict[guildid]["betweenTime"] = time
    channelsWrite[guildid] = channelsDict[guildid]
    await ctx.send(f"Rock Paper Scissors time between games has been set to {time} seconds!")

bot.run(TOKEN)