import random
import json

class PremadeParsers():
	def __init__(self):
		with open("Resources/emoji-mappings.json", encoding="utf8") as f:
		  self.emojisMap = json.load(f)

	def emojify(self, text):
		words = text.split()

		skipCount = 0
		newContent = ""
		for w in words:
			newContent = newContent + w
			keyToMatch = w.lower()
			if keyToMatch in self.emojisMap:
				newContent = newContent + " " + random.choice(self.emojisMap[keyToMatch]) + " "
				skipCount = 0
			elif skipCount < 1:
				newContent = newContent + " "
				skipCount = skipCount + 1
			else:
				randomKey = random.choice(list(self.emojisMap.keys()))
				newContent = newContent + " " + random.choice(self.emojisMap[randomKey]) + " "
				skipCount = 0	

		return newContent
	
	def uwuify(self, text):
		text = text.replace("you ", "yuw ")
		text = text.replace("l", "w")
		text = text.replace("r", "w")
		text = text.replace("no", "nyo")
		text = text.replace("na", "nya")

		words = text.split()

		fillerWords = [" uwu", " owo", ", *pounces you*,", ", *snozzles*,", ", *purrs*,", " ***GLOMP***"]

		wordCount = 0
		newContent = ""
		for w in words:
			newContent = newContent + w
			wordCount = wordCount + 1
			if wordCount >= 5 and random.randint(0, 3) == 0:
				wordCount = 0
				newContent = newContent + random.choice(fillerWords) + " "
			else:
				newContent = newContent + " "
		
		return newContent