import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import random
from premade_parsers import premade_parsers
from custom_curse import *

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(level=logging.INFO)

#Create classes
premade_parsers_instance = premade_parsers()

commandPrefix = '??'
bot = commands.Bot(command_prefix=commandPrefix)

#Helper functions
def get_user_folder(user):
	return "Custom_Curses/" + str(user.id)

#Premade parsers
@bot.command(name='curse_emoji', help='Curse a message with emojis')
async def curse(ctx):
	contentToCurse = ctx.message.content.replace("??curse_emoji ", "")
	new_content = premade_parsers_instance.emojify(contentToCurse)
	
	await ctx.message.delete()
	await ctx.send(ctx.author.display_name + ": " + new_content)

@bot.command(name='curse_uwu', help='Snuggles and pounces on your text uwu')
async def uwu(ctx):
	contentToCurse = ctx.message.content.replace("??curse_uwu ", "")
	new_content = premade_parsers_instance.uwuify(contentToCurse)
	
	await ctx.message.delete()
	await ctx.send(ctx.author.display_name + ": " + new_content)

#Custom curse commands
@bot.command(name='curse_custom', help='Snuggles and pounces on your text uwu')
async def custom(ctx):
	contentToCurse = ctx.message.content.replace("??curse_custom ", "")

	new_custom_curse = custom_curse()
	new_custom_curse.rules.append(custom_curse_rule_replace("l", "w"))
	new_custom_curse.rules.append(custom_curse_rule_replace("r", "w"))
	new_custom_curse.rules.append(custom_curse_rule_insert("uwu", 3))

	new_content = new_custom_curse.parse(contentToCurse)

	rootFolder = get_user_folder(ctx.author)
	if not os.path.exists(rootFolder):
		os.makedirs(rootFolder)
	
	fileNameWithFolder = rootFolder + "/test_curse.json"
	with open(fileNameWithFolder, 'w') as f:
		f.write(new_custom_curse.get_json_string())
	
	await ctx.message.delete()
	await ctx.send(ctx.author.display_name + ": " + new_content)

@bot.command(name='curse_custom_use', help='Snuggles and pounces on your text uwu')
async def custom_use(ctx):
	contentToCurse = ctx.message.content.replace("??curse_custom_use ", "")

	new_custom_curse = custom_curse()
	
	file_location = get_user_folder(ctx.author) + "/test_curse.json"
	with open(file_location, 'r') as f:
		file_read_data = f.read()
		json_data = json.loads(file_read_data)
		new_custom_curse.create_from_json(json_data)
	
	new_content = new_custom_curse.parse(contentToCurse)
	
	await ctx.message.delete()
	await ctx.send(ctx.author.display_name + ": " + new_content)

bot.run(TOKEN)