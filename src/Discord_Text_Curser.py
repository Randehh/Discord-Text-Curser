import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import random
import DiscordUtils
from PremadeParsers import PremadeParsers

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MODEL_NAME = "124M"

logging.basicConfig(level=logging.INFO)

#Create classes
premade_parsers = PremadeParsers()

commandPrefix = '??'
bot = commands.Bot(command_prefix=commandPrefix)

@bot.command(name='curse_emoji', help='Curse a message with emojis')
async def curse(ctx):
	contentToCurse = ctx.message.content.replace("??curse_emoji ", "")
	newContent = premade_parsers.emojify(contentToCurse)
	
	await ctx.message.delete()
	await ctx.send(ctx.author.display_name + ": " + newContent)

@bot.command(name='curse_uwu', help='Snuggles and pounces on your text uwu')
async def uwu(ctx):
	contentToCurse = ctx.message.content.replace("??curse_uwu ", "")
	newContent = premade_parsers.uwuify(contentToCurse)
	
	await ctx.message.delete()
	await ctx.send(ctx.author.display_name + ": " + newContent)

bot.run(TOKEN)