import os
import logging

import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv
import json
import random
import file_utils
from conversation_manager import conversation_manager
from conversations import conversation_base, conversation_main_menu, conversation_create_curse
import conversation_utils
import user_metadata
import curse_vote_database

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DEVELOPER_MODE = os.getenv('DEVELOPER_MODE')

logging.basicConfig(level=logging.INFO)

#Create classes
conversation_manager_instance = conversation_manager()
conversation_base.conversation_manager = conversation_manager_instance

curse_vote_database.load_latest()
user_metadata.load_latest()

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
		if not await conversation_manager_instance.process_message(message.author.id, message):
			await conversation_main_menu(message.author).start_conversation()
	else:
		enabled_curse = user_metadata.get_enabled_curse(message.author)
		if enabled_curse:
			await conversation_utils.replace_message_with_curse(message, enabled_curse)

##########################################
# Commands to get the conversation flowing (hehe)
##########################################
@bot.command(name='curse_menu', help='Starts the main menu flow')
async def custom_curse_menu(ctx):
	await conversation_main_menu(ctx.author).start_conversation()

##########################################
# Loop for routine events
##########################################
async def backup_routine():
	delay = 60 * 30 	# Once per half an hour
	if DEVELOPER_MODE == 1:
		delay = 60		# Once per minute

	while True:
		await asyncio.sleep(delay)
		curse_vote_database.save_backup()
		user_metadata.save_backup()

async def close_conversations_routine():
	delay = 60
	while True:
		await asyncio.sleep(delay)
		await conversation_manager_instance.attempt_close_conversations()

asyncio.get_event_loop().create_task(backup_routine())
asyncio.get_event_loop().create_task(close_conversations_routine())
bot.run(TOKEN)