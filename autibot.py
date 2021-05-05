import discord
import os
import re
import fileinput
import random
from discord.ext import commands
from pprint import pprint
from typing import List

# TODO VÄHÄN PAREMMAT DATABASET VOIS OLLA JO KIVA TÄSSÄ VAIHEESSA EIKÄ TÄMMÖSTÄ .TXT SÄÄTÖÄ
# TODO ROLLIMÄÄRÄ PITÄS TALLENTAA MYÖS LAST_PLAYERSIIN JA REMATCH FUNKTION KÄYTTÄÄ SITÄ
# TODO TEEMO DATABASE -FILELLA PITÄS OLLA PAREMPI NIMI

#Files
BOT_TOKEN_FILE = "bot_token.txt"
ALL_CHAMPS_FILE = "all_champs.txt"
TEEMO_DB_FILE = "database.txt"
PLAYER_CHAMP_DB_FILE = "player_champ_database.txt"
LAST_PLAYERS_FILE = "last_players.txt"
# Other constants
ARPE_EMOJI_URLS = ["https://cdn.discordapp.com/emojis/397083734731653123.png",
                   "https://cdn.discordapp.com/emojis/387365033216049165.png",
                   "https://cdn.discordapp.com/emojis/613082979513663489.png",
                   "https://cdn.discordapp.com/emojis/729836547343384596.png",
                   "https://cdn.discordapp.com/emojis/533366058933813259.png"]
ARPE_LAUSAHDUKSET = ["Joo swainilla eniten damagee",
                     "Tuijottiko se kummallakin korvalla?",
                     "Haluutko kuulla miltä mutakakku maistuu?",
                     "Saska, vitun pönttöpää saatana",
                     "Identivoidun naiseksi",
                     "Eiks koirat raksuta",
                     "Parempi raita pöntössä kun kaks housuissa",
                     "Jos kaikki on harmaata paskaa niin siitä on vaikee löytää puhasta kultaa",
                     "Gk fjk äHMg",
                     "http://keskustelu.suomi24.fi/t/12436852/haemme-suomalaisia-pelaajia-wot-klaaniin-(psop-panssarisopulit)",
                     "kyllä, se oli suomiopillisesti ihan täydellisesti sanottu"]
HELP_STRINGS = {"aram": f"""Makes aram teams with given (2 or more) players
                            **Usage:** +aram [rolls] player...""",
                "rematch": f"""Makes new aram game with same players
                               **Usage:** +rematch""",
                "roll": f"""Roll champions for given player(s)
                            **Usage:** +roll [rolls] [player...]"""
                }
GITHUB_URL = "https://github.com/Vahv1/panssarisipuli_bot"
REMATCH_ALIASES = ["paraskolmesta", "parasviiestä", "parasseittemästä", "paraskolmestatoista"]
VAINO_URLS = ["https://i.imgur.com/Jk2GhQh.jpeg", "https://i.imgur.com/VkhvTLL.jpeg"]

client = discord.Client()
bot = commands.Bot(command_prefix='+')

def init_all_champs_list():
    """
    Return a list of all champions that is stored in all_champs .txt file
    """
    with open(ALL_CHAMPS_FILE, 'r') as f:
        return [line.strip() for line in f]

def init_bot_token():
    """
    Return bot token stored in .txt file
    """
    with open(BOT_TOKEN_FILE, 'r') as f:
        return [line.strip() for line in f][0]

ALL_CHAMPS = init_all_champs_list()
ALL_CHAMPS_LOWER = [x.lower() for x in ALL_CHAMPS]
BOT_TOKEN = init_bot_token()

open(PLAYER_CHAMP_DB_FILE, "w+") # create player champ db if doesn't exist

@bot.command(name='addchampions', aliases=['addchamps', 'addchamp', 'addchampion'])
async def add_champs(ctx, player, *champs):
    # TODO varmaan pystyy lisään duplikaattichamppeja atm
    """
    Add champions for a player.
    If 'all' parameter is used after player name, adds all champions except the ones given after it.
    :param player: name of player
    :param champs: champions to add for the player, champs[0] is checked for all-parameter
    """
    # List to store alias names for parameter word that must be given when adding all champions
    all_champs_param_aliases = ['all', 'kaikki']
    # Autism check: if more champions given than exist, do nothing
    if len(champs) > len(ALL_CHAMPS):
        await ctx.send(f"Mitä vittua nyt taas, ei noin montaa champpia oo ees olemassa")

    champs = [champ.lower() for champ in champs]  # change list to lower case

    # If all-parameter is given, edit champs list to contain all EXCEPT the given champs
    if champs[0] in all_champs_param_aliases:
        print("annettiin all")
        champs = sorted(list(set(ALL_CHAMPS_LOWER) - set(champs)))
    else:
        champs = [champ for champ in champs if champ in ALL_CHAMPS_LOWER]  # remove invalid champ names
        champs = sorted(list(set(champs)))  # remove duplicate champ names

    set_player_champions(player, champs)

    await ctx.send(f"Added {str(champs)} for player {player}")
    
@bot.command(name='addaliases', aliases=['addalias'])
async def add_aliases(ctx, player, *aliases):
    """
    Add aliases for a player.
    :param player: existing name of the player
    :param aliases: aliases to add for the player
    """
    set_player_aliases(player, aliases)
    await ctx.send(f"Added aliases {str(aliases)} for {player}")

@bot.command(name='aram')
async def make_aram_teams(ctx, *args):
    """
    Makes aram teams from given discord user mentions and prints them to channel
    :param ctx: context of discord command given
    :param args: first argument is champions rolls
    """
    rolls = 3
    players = []

    if len(args) > 1:
        # if first argument is digit it defines roll amount, otherwise is player name
        if args[0].isdigit():
            rolls = int(args[0])
        else:
            players.append(args[0])

        for player in args[1:]:
            players.append(player)
    else:
        await ctx.send("Jossei osaa nii kannattaa lukee ohjeet (+aramhelp)")

    # TODO if random teams feature is implemented, player list must be randomized before this
    # so that save teams will correctly save the randomized team.
    save_teams(players)
    embed = make_embed(players, rolls)
    await ctx.send(embed=embed)

@bot.command(name='aramhelp')
async def help(ctx):
    """
    Sends message with info how to use this bot
    """
    help_description = f"""[parameter] is optional parameter
                           parameter... means multiple parameters can be given"""

    embed = discord.Embed(title="Hjälp",
                          colour=discord.Colour(0x42DDE5),
                          description=help_description)
    for key in HELP_STRINGS:
        embed.add_field(name=key, value= HELP_STRINGS[key], inline=False)
    await ctx.send(embed=embed)

@bot.command(name='rematch', aliases=REMATCH_ALIASES)
async def rematch(ctx):
    """
    Makes aram game with new champs but same teams as last game and prints them to channel
    :param ctx: context of discord command given
    """
    rolls = 3
    # Get player list from last game
    players = get_last_game_players()
    embed = make_embed(players, rolls)
    await ctx.send(embed=embed)

@bot.command(name='reroll', aliases=['roll'])
async def reroll(ctx, *args):
    """
    Rolls new champions for given player or command caller if no parameters given
    :param args: players to roll champs for. NOTE! If first argument is digit,
                 thats amount of champs rolled.
    """
    rolls = 3
    player_list = []

    if args:
        # if first argument is digit it defines roll amount, otherwise is player name
        if args[0].isdigit():
            rolls = int(args[0])
        else:
            player_list.append(args[0])

        if len(args) > 1:
            for player in args[1:]:
                player_list.append(player)

    # If no players given as argument, player is message sender
    if len(player_list) == 0:
        player_list = [ctx.message.author.name]

    embed = make_reroll_embed(player_list, rolls)
    await ctx.send(embed=embed)

@bot.command(name='champions', aliases=['champs'])
async def print_champs(ctx, player):
    """
    Prints a list of player's champions.
    :param player: name of player
    """
    try:
        player_aliases = get_player_aliases(player)
        player_champs = sorted([champ.capitalize() for champ in get_player_champions(player)])
        await ctx.send(f"{player_aliases[0]} ({(player_aliases[1:])}) champions ({len(player_champs)}): {str(player_champs)}")
    except ValueError:
        await ctx.send("No player with that name exists in database")

@bot.command(name='resetchampions', aliases=['resetchamps'])
async def reset_champions(ctx, player):
    """
    Reset champions stored for a player in database.
    :param player: name or alias of existing player in database
    """
    player_found_in_database = False
    player_name = player.lower()
    player_champ_db = open(PLAYER_CHAMP_DB_FILE, "r")
    lines = player_champ_db.readlines()
    for i in range(len(lines)):
        player_aliases = lines[i].split(';')[0].split(',')
        if player_name in player_aliases:
            player_found_in_database = True
            lines[i] = ','.join(player_aliases) + ";" + "\n"
            new_db_line = lines[i]

    database = open(PLAYER_CHAMP_DB_FILE, "w")
    database.writelines(lines)
    if player_found_in_database:
        await ctx.send(f"Champions list reset for player {player}")
    else:
        await ctx.send(f"No player with name {player} found in database. Use '+addchamps player_name champ...' to add new player")

@bot.command(name='source', aliases=['github', 'code'])
async def source_code(ctx):
    await ctx.send(GITHUB_URL)

def database_line(aliases, champs):
    """
    Get correctly formatted str to add as line to player champion database
    :param aliases: list of aliases for player
    :param champs: list of champions for player
    :return: formatted str
    """
    return ','.join(aliases) + ";" + ','.join(champs) + "\n"

def get_last_game_players():
    """
    Gets player list of last game from saved txt-file
    """
    last_players_file = open(LAST_PLAYERS_FILE, "r")
    last_players = last_players_file.read().split(';')
    last_players_file.close()
    return last_players

def get_player_aliases(player):
    """
    Get aliases for given player from database.
    :param player: player name
    :return: list of aliases including the given player name
    """
    player_name = player.lower()
    player_champ_db = open(PLAYER_CHAMP_DB_FILE, "r")
    lines = player_champ_db.readlines()
    for i in range(len(lines)):
        player_aliases = lines[i].split(';')[0].split(',')
        if player_name in player_aliases:
            return player_aliases
    raise ValueError("Player not found in database")

def get_player_champions(player):
    """
    Get list of player champions from database
    :param player: player name
    :return: list of player champions
    """
    player_name = player.lower()
    player_champ_db = open(PLAYER_CHAMP_DB_FILE, "r")
    lines = player_champ_db.readlines()
    for line in lines:
        player_aliases = line.split(';')[0].split(',')
        if player_name in player_aliases:
            player_champs = line.rstrip().split(';')[1].split(',')
            player_champs = [champ for champ in player_champs if champ]  # remove empty items
            return player_champs
    raise ValueError("Player not found in database")

def make_embed(player_list: List[str], rolls):
    """
    Makes discord embed message that shows teams and rolled champs.
    :param champ_dict: List that contains player names
    :return: discord embed that contains formatting for sending a message with aram teams
    """
    champ_dict = roll_player_champs(player_list, rolls)
    player_names = list(champ_dict.keys())
    player_champs = list(champ_dict.values())
    player_amount = len(champ_dict)

    team_1_players_text = ""
    team_1_champs_text = ""
    team_2_players_text = ""
    team_2_champs_text = ""

    # Set player and champions texts
    for i in range(player_amount):
        if i*2 < player_amount:  # Add first half of players to team 1
            team_1_players_text += f"**{player_names[i]}** \n"
            team_1_champs_text += f"{', '.join(player_champs[i])} \n"
        else:
            team_2_players_text += f"**{player_names[i]}** \n"
            team_2_champs_text += f"{', '.join(player_champs[i])} \n"

    # Create embed message to send to discord
    embed = discord.Embed(title="Aaram",  colour=discord.Colour(0x42DDE5))
    embed.add_field(name="Team 1", value=team_1_players_text, inline=True)
    embed.add_field(name="\u200b", value=team_1_champs_text, inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=False) # Empty field to separate teams
    embed.add_field(name="Team 2", value=team_2_players_text, inline=True)
    embed.add_field(name="\u200b", value=team_2_champs_text, inline=True)

    return embed

def make_reroll_embed(players: str, rolls):
    """
    Makes discord embed message that shows new rolled champs for player
    :param player: name of player who is rolling
    """
    champ_dict = roll_player_champs(players, rolls)
    player_names = list(champ_dict.keys())
    player_champs = list(champ_dict.values())

    embed = discord.Embed(title="Reroll",  colour=discord.Colour(0x42DDE5))
    for player in player_names:
        player_champs = ', '.join(champ_dict[player])
        embed.add_field(name=player, value=player_champs, inline=False)
    return embed

def roll_player_champs(players: List[str], rolls=3):
    """
    Get dictionary of all players and list of champions rolled for them.
    :param players: list of players names
    :return: {player_name: [champions]} dictionary
    """
    player_champ_picks = {}  # {nepa: [ahri, amumu, azir], saska: [zoe, zyra, zed]}
    all_rolled_champs = []

    # Roll a champion for everyone and add to dictionary
    for p in players:
        rolled_champs = []
        i = 0
        while (i < rolls):
            champ = random.choice(ALL_CHAMPS)
            if (champ not in all_rolled_champs):
                rolled_champs.append(champ)
                all_rolled_champs.append(champ)
                i += 1
        player_champ_picks[p] = sorted(rolled_champs)

    if "Teemo" in rolled_champs:
        add_to_teemo_counter()

    return player_champ_picks

def save_teams(players: List[str]):
    """
    Saves player list to text file so new champs can be rolled to same teams
    without giving all players as parameters again.
    File is formatted as: player1;player2;player3
    """
    last_players_file = open(LAST_PLAYERS_FILE, "w+")
    last_players_file.write(';'.join(players))
    last_players_file.close()

def set_player_aliases(player, aliases):
    """
    Sets list of new aliases including given player name for player in database.
    Creates ne player to database if given name does not exist
    :param player: aliases to set
    """
    player_name = player.lower()
    player_champ_db = open(PLAYER_CHAMP_DB_FILE, "r")
    lines = player_champ_db.readlines()
    try:
        new_aliases = get_player_aliases(player_name)
        new_aliases.extend(aliases)
        for i in range(len(lines)):
            player_aliases = lines[i].split(';')[0].split(',')
            if player_name in player_aliases:
                player_champs = get_player_champions(player_name)
                lines[i] = database_line(new_aliases, player_champs)
    except ValueError:
        lines.append(database_line([player] + list(aliases), ""))

    database = open(PLAYER_CHAMP_DB_FILE, "w")
    database.writelines(lines)

def set_player_champions(player, champs):
    """
    Sets list of champions for player in database
    :param player: player name
    :param champions: list of champions to set
    """
    player_name = player.lower()
    player_champ_db = open(PLAYER_CHAMP_DB_FILE, "r")
    lines = player_champ_db.readlines()
    try:
        new_champs = get_player_champions(player_name)
        new_champs.extend(champs)
        # Check database for player name and add new champions if found
        for i in range(len(lines)):
            player_aliases = lines[i].split(';')[0].split(',')
            if player_name in player_aliases:
                lines[i] = database_line(player_aliases, new_champs)
        # Add new line to database if player name was not found in database
    except ValueError:
        lines.append(database_line([player], champs))

    database = open(PLAYER_CHAMP_DB_FILE, "w")
    database.writelines(lines)
    
####  USELESS COMMANDS ####

@bot.command(name='tuopallo')
async def teuvo(ctx):
    embed = discord.Embed(title="Vuh vuh!", 
                          description="",
                          colour=discord.Colour(0x42DDE5))
    embed.set_image(url="https://i.imgur.com/ycU1qF4.png")
    await ctx.send(embed=embed)
    

@bot.command(name='topugetir')
async def teuvo(ctx):
    embed = discord.Embed(title="Hav hav!", 
                          description="",
                          colour=discord.Colour(0x42DDE5))
    embed.set_image(url="https://i.imgur.com/iAfRLeT.png")
    await ctx.send(embed=embed)
    
@bot.command(name='silitäväinöä')
async def teuvo(ctx):
    embed = discord.Embed(title="Mau", 
                          description="",
                          colour=discord.Colour(0x42DDE5))
    embed.set_image(url=random.choice(VAINO_URLS))
    await ctx.send(embed=embed)
    
@bot.command(name='golf', aliases=['golffi'])
async def golf(ctx):
    if len(ctx.message.attachments) > 0:
        att = ctx.message.attachments[0] # Only check for first attachment
        att_name = att.filename
        
        # Check correct file extension
        if att_name.endswith(".txt"):
        
            # Save attachment if it was .txt
            save_file_name = "golfmap.txt"
            await att.save(fp=save_file_name)

            # read file to a string and split from : and , to get coordinates as list elements
            map_text = open("golfmap.txt", "r").read()
            line_split = re.split(':|,', map_text)
            
            invalid_coords = []
            # Add all coordinates above wanted threshold to invalid_coords list
            for splitti in line_split:
                try:
                    if abs(float(splitti)) > 250:
                        invalid_coords.append(splitti)
                except ValueError:
                    pass
            
            # Send invalid coordinates as message
            coord_message = " ".join(invalid_coords)
            await ctx.send(coord_message)
        else:
            await ctx.send("Liite pitää olla .txt")
    else:
        await ctx.send("Laita .txt tiedosto mukaan")
    
@bot.command(name='arpe', aliases=['pepega', 'fourpette', 'itsyourtime', 'swain'])
async def arpe(ctx):
    embed = discord.Embed(title="4rpe", 
                          description=random.choice(ARPE_LAUSAHDUKSET),
                          colour=discord.Colour(0x42DDE5))
    embed.set_image(url=random.choice(ARPE_EMOJI_URLS))
    await ctx.send(embed=embed, delete_after=10)
    
@bot.command(name='teemo')
async def teemo(ctx):
    database = open(TEEMO_DB_FILE, "r")
    lines = database.readlines()
    amt = 0
    for line in lines:
        if "teemo" in line:
            amt = int(line.split(';')[1])
    await ctx.send(f"Teemo rollattu {amt} kertaa")

def add_to_teemo_counter():
    database = open(TEEMO_DB_FILE, "r")
    lines = database.readlines()
    for i in range(len(lines)):
        if "teemo" in lines[i]:
            amt = int(lines[i].split(';')[1])
            amt += 1
            lines[i] = f"teemo;{amt}"

    database = open(TEEMO_DB_FILE, "w")
    database.writelines(lines)

bot.run(BOT_TOKEN)
