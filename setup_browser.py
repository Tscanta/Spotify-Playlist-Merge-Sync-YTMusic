import ytmusicapi

# Your cookie string
cookie_string="bp8LckHzZty4W7VE/AVgQEIslVb51IR7SY"
try:
    # Use ytmusicapi.setup instead of YTMusic.setup
    ytmusicapi.setup(filepath="browser.json", headers_raw=cookie_string)
    print("Success! 'browser.json' has been created.")
except Exception as e:
    print(f"Error creating browser.json: {e}")