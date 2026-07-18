import re
import requests
import frappe

@frappe.whitelist()
def resolve_map_coordinates(url):
	resp = requests.head(url, allow_redirects=True, timeout=5)
	match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", resp.url)
	if not match:
		return None
	return {"latitude": float(match.group(1)), "longitude": float(match.group(2))}