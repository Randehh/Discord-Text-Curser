from discord import Webhook, RequestsWebhookAdapter
import requests
import os
from enum import IntEnum
import file_utils

guild_webhook_ids = {}

def get_curses_for_user(user_id):
	files = file_utils.get_files_for_user_id(user_id)
	for index, file_name in enumerate(files):
		files[index] = file_name.replace(".json", "")
	return files

def get_list_options(list, headers = {}):
	message = "```"
	count = 0
	for value in list:		
		if count in headers:
			if count != 0:
				message = message + "\n"
			message = message + headers[count] + "\n"
		
		pretty_enum_name = value.replace("_", " ").title()
		message = message + str(count + 1) + ":\t" + pretty_enum_name + "\n"
		
		count = count + 1
	return message + "```"

def get_enum_options(enum, headers = {}):
	message = "```"
	count = 0
	for enum_value in enum:
		if enum_value.value == -1:
			continue
		
		if count in headers:
			if count != 0:
				message = message + "\n"
			message = message + headers[count] + "\n"
		
		pretty_enum_name = enum_value.name.replace("_", " ").title()
		message = message + str(enum_value.value) + ":\t" + pretty_enum_name + "\n"
		
		count = count + 1
	return message + "```"

async def get_conversation_webhook(channel):
	if not channel.guild.id in guild_webhook_ids:
		return await create_new_webhook(channel)
	
	webhook_id = guild_webhook_ids[channel.guild.id]
	hooks = await channel.guild.webhooks()
	for hook in hooks:
		try:
			if hook.id == webhook_id:
				return await update_webhook_channel(hook, channel)
		except AttributeError:
			continue
	
	return await create_new_webhook(channel)

async def create_new_webhook(channel):
	webhook = await channel.create_webhook(name = "Curser Hook")
	guild_webhook_ids[channel.guild.id] = webhook.id
	return webhook

async def update_webhook_channel(hook, target_channel):
	if hook.channel_id == target_channel.id:
		return hook
	
	BOT_TOKEN = os.getenv('DISCORD_TOKEN')
	WEBHOOK_ID = str(hook.id)

	json = { "channel_id": target_channel.id }
	headers = { "Authorization": "Bot " + BOT_TOKEN }

	requests.patch('https://discordapp.com/api/webhooks/' + WEBHOOK_ID, json=json, headers=headers)
	return hook

async def is_string_int(string, user):
	try: 
		int(string)
		return True
	except ValueError:
		await user.send(string + " is not a number.")
		return False

async def replace_message_with_curse(message, curse):
	await message.delete()
	webhook = await get_conversation_webhook(message.channel)

	user_avatar = message.author.avatar_url
	cursed_content = curse.parse(message.content)
	await webhook.send(cursed_content, username=message.author.display_name, avatar_url=user_avatar)