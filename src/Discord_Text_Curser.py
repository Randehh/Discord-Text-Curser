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

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

logging.basicConfig(level=logging.INFO)

#Create classes
file_utils_instance = file_utils()
conversation_manager_instance = conversation_manager()

commandPrefix = '??'
bot = commands.Bot(command_prefix=commandPrefix)

##########################################
# Custom curse creation flow
##########################################
@bot.command(name='curse_start', help='Starts creation of a new curse')
async def custom_curse_start(ctx):
	await ctx.message.delete()
	await ctx.author.send("Let's start creating a new curse.\n\nWhat would you like to name your curse?")

	conversation_manager_instance.start_conversation(ctx.author, on_curse_name_received)

async def on_curse_name_received(conversation_data, message):
	curse_name = message.content.lower().replace(" ", "_")
	new_curse = curse(curse_name)
	conversation_data["curse"] = new_curse

	message_to_send = "Creating new curse called: ***" + curse_name + "***\n\n"
	await conversation_data["author"].send(message_to_send)
	await start_new_rule_flow(conversation_data)

async def start_new_rule_flow(conversation_data):
	rule_options = get_rule_options()
	message_to_send = "What type of rule would you like to add?\n" + rule_options + "Reply with the number."

	author = conversation_data["author"]
	await author.send(message_to_send)

	conversation_manager_instance.set_callback_for_user(author, on_curse_rule_received)

async def on_curse_rule_received(conversation_data, message):
	new_rule = create_rule_from_type(int(message.content))
	await new_rule.request_parameters(conversation_data, on_curse_rule_params_set)

async def on_curse_rule_params_set(conversation_data, new_rule):
	conversation_data["curse"].rules.append(new_rule)

	author = conversation_data["author"]
	curse_description = conversation_data["curse"].get_rules_descriptions()
	await author.send(curse_description + "\nWould you like to add another rule?\nReply \"YES\" or \"NO\"")

	conversation_manager_instance.set_callback_for_user(author, on_curse_another_rule)

async def on_curse_another_rule(conversation_data, message):
	message_content = message.content.lower().strip()
	author = conversation_data["author"]

	if message_content == "yes":
		await start_new_rule_flow(conversation_data)
	elif message_content == "no":
		curse = conversation_data["curse"]
		file_utils_instance.create_file_for_user(conversation_data["author"], curse.name + ".json", curse.get_json_string())
		await author.send("New curse ***" + curse.name + "*** is saved.\nUse \"??curse_use " + curse.name + " <message to curse>\" to use the curse.")
		conversation_manager_instance.stop_conversation(author)
	else:
		await author.send("Response is not valid.\nReply \"YES\" or \"NO\"")

@bot.event
async def on_message(message):
	await bot.process_commands(message)
	if message.author.bot == True:
		return
	
	if not message.guild:
		await conversation_manager_instance.process_message(message.author, message)

def get_rule_options():
	message = ""
	for rule in rule_types:
		pretty_rule_name = rule.name.replace("_", " ").title()
		message = message + str(rule.value) + " - " + pretty_rule_name + "\n"
	return message

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

	conversation_data = conversation_manager_instance.start_conversation(ctx.author, on_curse_content_received)
	conversation_data["curse"] = new_custom_curse

async def on_curse_content_received(conversation_data, message):
	cursed_message = conversation_data["curse"].parse(message.content)

	author = conversation_data["author"]
	await author.send(cursed_message)
	conversation_manager_instance.stop_conversation(author)

bot.run(TOKEN)