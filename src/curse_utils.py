
def get_curse_id(user_id, curse_name):
    return str(user_id) + "#" + curse_name

def get_user_from_curse_id(curse_id):
	return int(curse_id.split("#")[0])

def get_name_from_curse_id(curse_id):
	return curse_id.split("#")[1]

async def is_string_int(string, user):
	try: 
		int(string)
		return True
	except ValueError:
		await user.send(string + " is not a number.")
		return False