import json

def load_data(path, key="employees"):
	"""Load the employees roster from JSON file"""
	key_data = []
	if path:
		print(f"📄 Loading roster from: {path}")
		with open(path, 'r') as f:
			data = json.load(f)
		key_data = data.get(key, [])
		print(f"  ✓ Loaded {len(key_data)} {key} from roster\n")
	return key_data

def load_json(path):
	"""Load entire JSON file and return the parsed dict"""
	if not path:
		return {}
	with open(path, 'r') as f:
		return json.load(f)