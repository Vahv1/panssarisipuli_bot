import discord
import os
import fileinput
import random
from discord.ext import commands
from pprint import pprint
from typing import List

# TODO ROLLIMÄÄRÄ PITÄS TALLENTAA MYÖS LAST_PLAYERSIIN JA REMATCH FUNKTION KÄYTTÄÄ SITÄ
# DELETE MESSAGES THAT CALLED BOT

BOT_TOKEN = "NjQ3ODgyMzM0NzA3Nzc3NTM2.XdmMQw.37fQcqubuF_8Z4Ruq9MkISnb-nY"
# Files
ALL_CHAMPS_FILE = "all_champs.txt"
DATABASE_FILE = "database.txt"
LAST_PLAYERS_FILE = "last_players.txt"
# Other constants
ARPE_EMOJI_URLS = ["https://cdn.discordapp.com/emojis/397083734731653123.png",
                   "https://cdn.discordapp.com/emojis/387365033216049165.png",
                   "https://cdn.discordapp.com/emojis/613082979513663489.png",
                   "https://cdn.discordapp.com/emojis/729836547343384596.png",
                   "https://cdn.discordapp.com/emojis/533366058933813259.png"]
ARPE_LAUSAHDUKSET = ["Joo swainilla eniten damagee"]
HELP_STRINGS = {"aram": f"""Makes aram teams with given (2 or more) players
                            **Usage:** +aram [rolls] player...""",
                "rematch": f"""Makes new aram game with same players
                               **Usage:** +rematch""",
                "roll": f"""Roll champions for given player(s)
                            **Usage:** +roll [rolls] [player...]"""
                }
REMATCH_ALIASES = ["paraskolmesta", "parasviiestä", "parasseittemästä", "paraskolmestatoista"]

client = discord.Client()
bot = commands.Bot(command_prefix='+')

def init_all_champs_list():
    """
    Return a list of all champions that is stored in all_champs.txt file
    # TODO add new champs to list
    """
    with open(ALL_CHAMPS_FILE, 'r') as f:
        return [line.strip() for line in f]

ALL_CHAMPS = init_all_champs_list()

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
    await ctx.send(embed=embed, delete_after=300)

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
        await ctx.send("Jossei osaa nii kannattaa lukee ohjeet (+aramhelp)", delete_after=300)
    
    # TODO if random teams feature is implemented, player list must be randomized before this
    # so that save teams will correctly save the randomized team.
    save_teams(players)
    embed = make_embed(players, rolls)
    await ctx.send(embed=embed, delete_after=300)
 
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
    await ctx.send(embed=embed, delete_after=300)
    
@bot.command(name='reroll', aliases=['roll'])
async def reroll(ctx, *args):
    """
    Rolls ne champions for given player or command caller if no parameters given
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
    await ctx.send(embed=embed, delete_after=300)
    
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

def get_last_game_players():
    """
    Gets player list of last game from saved txt-file
    """
    last_players_file = open(LAST_PLAYERS_FILE, "r")
    last_players = last_players_file.read().split(';')
    last_players_file.close()
    return last_players

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
    File is formatted as: player1;player2,player3
    """
    last_players_file = open(LAST_PLAYERS_FILE, "w+")
    last_players_file.write(';'.join(players))
    last_players_file.close()
    
####  USELESS COMMANDS ####
    
@bot.command(name='arpe')
async def arpe(ctx):
    embed = discord.Embed(title="4rpe", 
                          description=random.choice(ARPE_LAUSAHDUKSET),
                          colour=discord.Colour(0x42DDE5))
    embed.set_image(url=random.choice(ARPE_EMOJI_URLS))
    await ctx.send(embed=embed)
    
@bot.command(name='teemo')
async def teemo(ctx):
    database = open(DATABASE_FILE, "r")
    lines = database.readlines()
    amt = 0
    for line in lines:
        if "teemo" in line:
            amt = int(line.split(';')[1])
    await ctx.send(f"Teemo rollattu {amt} kertaa")

def add_to_teemo_counter():
    database = open(DATABASE_FILE, "r")
    lines = database.readlines()
    for i in range(len(lines)):
        if "teemo" in lines[i]:
            amt = int(lines[i].split(';')[1])
            amt += 1
            lines[i] = f"teemo;{amt}"

    database = open(DATABASE_FILE, "w")
    database.writelines(lines)

bot.run(BOT_TOKEN)
