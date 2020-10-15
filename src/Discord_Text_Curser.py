import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import random
import file_utils
from conversation_manager import conversation_manager
from curse import *
from conversations import  *
import conversation_utils
import user_metadata

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(level=logging.INFO)

#Create classes
conversation_manager_instance = conversation_manager()
conversation_base.conversation_manager = conversation_manager_instance

commandPrefix = '??'
bot = commands.Bot(command_prefix=commandPrefix)

##########################################
# Message processing initialization
##########################################
@bot.event
async def on_message(message):
	if message.author.bot == True:
		return

	await bot.process_commands(message)
	
	if not message.guild:
		await conversation_manager_instance.process_message(message.author, message)
	else:
		enabled_curse = await user_metadata.get_enabled_curse(message.author)
		if enabled_curse:
			await conversation_utils.replace_message_with_curse(message, enabled_curse)

##########################################
# Commands to get the conversation flowing (hehe)
##########################################
@bot.command(name='curse_menu', help='Starts the main menu flow')
async def custom_curse_menu(ctx):
	await conversation_main_menu(ctx.author).start_conversation()

@bot.command(name='curse_start', help='Starts creation of a new curse')
async def custom_curse_start(ctx):
	await conversation_create_curse(ctx.author).start_conversation()

bot.run(TOKEN)