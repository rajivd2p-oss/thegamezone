# thegamezone

Airtag tracker + web API for Hack Club the Game, a 100 player Jet Lag inspired adventure across Manhattan.

## Usage
0. Install dependencies with `python3 pip install -r requirements.txt`
1. Fill out `EMAIL` and `PASSWORD` in `.env`, as well as a random generated string for `GAME_API_TOKEN`.
2. Generate your account session using `python3 account.py`.
3. Dump the accessory info from your Mac. If you have a Mac running MacOS 14 or under, great! Run `python3 -m findmy decrypt --out-dir devices/`. Otherwise, follow the instructions [here](https://docs.mikealmel.ooo/FindMy.py/getstarted/02-fetching.html), or use a VM running MacOS 14 or under (i.e [this one](https://github.com/sickcodes/Docker-OSX)) (may take 1-2 hours to set up) and put the .json files in the `devices` subdirectory of this folder. 
4. Start the API with `flask run`.


## Notes
Airtags all need to be attached to the same Apple account to work. This Apple Account must not have passkey authentication on. We recommend using a dummy account.

They don't need to be actual Airtags, but they do need to be compatible with the Apple Find My Network. 
