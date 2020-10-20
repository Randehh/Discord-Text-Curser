
def get_curse_id(user_id, curse_name):
    return str(user_id) + curse_name

async def is_string_int(string, user):
	try: 
		int(string)
		return True
	except ValueError:
		await user.send(string + " is not a number.")
		return False