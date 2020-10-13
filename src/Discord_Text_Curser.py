import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import random
from file_utils import file_utils
from conversation_manager import conversation_manager
from curse import *
from conversations import  *

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(level=logging.INFO)

#Create classes
file_utils_instance = file_utils()
conversation_manager_instance = conversation_manager()
conversation_base.conversation_manager = conversation_manager_instance
conversation_base.file_utils_instance = file_utils_instance

commandPrefix = '??'
bot = commands.Bot(command_prefix=commandPrefix)

##########################################
# Message processing initialization
##########################################
@bot.event
async def on_message(message):
	await bot.process_commands(message)
	if message.author.bot == True:
		return
	
	if not message.guild:
		await conversation_manager_instance.process_message(message.author, message)

##########################################
# Commands to get the conversation flowing (hehe)
##########################################
@bot.command(name='curse_menu', help='Starts the main menu flow')
async def custom_curse_menu(ctx):
	await conversation_main_menu(ctx.author).start_conversation()

@bot.command(name='curse_start', help='Starts creation of a new curse')
async def custom_curse_start(ctx):
	await conversation_create_curse(ctx.author).start_conversation()

##########################################
# Custom curse usage
##########################################
@bot.command(name='curse_use', help='Snuggles and pounces on your text uwu')
async def custom_use(ctx, curse_name):	
	json_data_raw = file_utils_instance.read_file_for_user(ctx.author, curse_name + ".json")
	json_data = json.loads(json_data_raw)

	new_custom_curse = curse(curse_name)
	new_custom_curse.create_from_json(json_data)

	await ctx.message.delete()
	await ctx.author.send("What would you like to ***" + curse_name + "***-ify?")

	#conversation_data = conversation_manager_instance.start_conversation(ctx.author, on_curse_content_received)
	#conversation_data["curse"] = new_custom_curse

async def on_curse_content_received(conversation_data, message):
	cursed_message = conversation_data["curse"].parse(message.content)

	author = conversation_data["author"]
	await author.send(cursed_message)
	conversation_manager_instance.stop_conversation(author)

bot.run(TOKEN)