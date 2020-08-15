import discord
import os
import fileinput
import random
from discord.ext import commands
from pprint import pprint
from typing import List

ARPE_EMOJI_URLS = ["https://cdn.discordapp.com/emojis/397083734731653123.png",
                   "https://cdn.discordapp.com/emojis/387365033216049165.png",
                   "https://cdn.discordapp.com/emojis/613082979513663489.png",
                   "https://cdn.discordapp.com/emojis/729836547343384596.png",
                   "https://cdn.discordapp.com/emojis/533366058933813259.png"]
ARPE_LAUSAHDUKSET = ["Joo swainilla eniten damagee"]
BOT_TOKEN = "NjQ3ODgyMzM0NzA3Nzc3NTM2.XdmMQw.37fQcqubuF_8Z4Ruq9MkISnb-nY"
ALL_CHAMPS_FILE = "all_champs.txt"
DATABASE_FILE = "database.txt"
LAST_PLAYERS_FILE = "last_players.txt"
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

@bot.command(name='aram')
async def make_aram_teams(ctx):
    """
    Makes aram teams from given discord user mentions and prints them to channel
    :param ctx: context of discord command given
    """
    players = ctx.message.content.split()[1:]
    # TODO if random teams feature is implemented, player list must be randomized before this
    # so that save teams will correctly save the randomized team.
    save_teams(players)
    embed = make_embed(players)
    await ctx.send(embed=embed)
 
@bot.command(name='rematch')
async def rematch(ctx):
    """
    Makes aram game with new champs but same teams as last game and prints them to channel
    :param ctx: context of discord command given
    """
    # Get player list from last game
    players = get_last_game_players()
    embed = make_embed(players)
    await ctx.send(embed=embed)
    
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
    
def make_embed(player_list: List[str]):
    """
    Makes discord embed message that shows teams and rolled champs.
    :param champ_dict: List that contains player names
    :return: discord embed that contains formatting for sending a message with aram teams
    """
    champ_dict = roll_player_champs(player_list)
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

def get_last_game_players():
    """
    Gets player list of last game from saved txt-file
    """
    last_players_file = open(LAST_PLAYERS_FILE, "r")
    last_players = last_players_file.read().split(';')
    last_players_file.close()
    return last_players

def roll_player_champs(players: List[str]):
    """
    Get dictionary of all players and list of champions rolled for them.
    :param players: list of players names
    :return: {player_name: [champions]} dictionary
    """
    rerolls = 2
    player_champ_picks = {}  # {nepa: [ahri, amumu, azir], saska: [zoe, zyra, zed]}
    all_rolled_champs = []
    
    # Roll a champion for everyone and add to dictionary
    for p in players:
        rolled_champs = []
        i = 0
        while (i < rerolls + 1):
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
    
####

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
