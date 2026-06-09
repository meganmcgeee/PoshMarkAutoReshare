# Closet Reshare
================
- Short Python script to auto share on Poshmark, written for my wife.

  ### REQUIRES TO RUN IN DEBUG MODE, WITH BREAK POINT SET.
- set break on print for captcha, yes I know this is a stupid way of catching but whatever
- TODO
  - Fix how captcha is handled, make dynamic.
  - add support for checks for random MFA requests when logging in
  - Fix static timed pauses, change to dynamic based on page response time


Logs in, goes to closet, selects only available items and reshares.

Run closet reshare with:

```bash
export POSHMARK_USERNAME="your-poshmark-username-or-email"
export POSHMARK_PASSWORD="your-poshmark-password"
python actions/closet_reshare.py
```

## Web UI

For a simpler and more visual way to run these scripts, you can use the built-in web UI.
It provides a sleek interface to input your credentials and launch any of the automation scripts.

To start the Web UI, run:
```bash
python app.py
```
Then, open your browser to `http://localhost:5000`.

## Other actions

### Feed Reshare (`actions/feed_reshare.py`)

This script allows you to auto-share listings from your main feed, a brand page, or another user's closet.
1. Run `python actions/feed_reshare.py`
2. Follow the prompt to choose the source (1 = main feed, 2 = brand page, 3 = user's closet).
3. The script will automatically scroll to load the listings. For brand/user pages, it limits scrolling to 20 scrolls to avoid getting stuck.
4. You will be prompted to confirm when all desired listings are visible.
5. The script will share listings in batches of 10, pausing for 45 seconds between batches to avoid rate limits.

### Follow Users (`actions/follow_users.py`)

This script follows sellers from a brand page.
- Run `python actions/follow_users.py`
- It operates in batches of 10, with necessary pauses.

## Insights

- `insights/top_liked_brand_listings.py`: log in, go to a brand page, and print the URLs of the most liked listings on that page.

