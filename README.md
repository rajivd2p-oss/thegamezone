# thegamezone

Airtag tracker + web API. Made for Hack Club the Game, a 100 player Jet Lag inspired adventure across Manhattan.

## Usage
1. Install dependencies with `python3 pip install -r requirements.txt` (in a virtual environment, you get the deal)
2. Fill out `EMAIL` and `PASSWORD` in `.env`, as well as a random generated string for `GAME_API_TOKEN`. You can remove `EMAIL` and `PASSWORD` after you complete Step 3.
3. Generate your encoded account session using `python3 account.py`.
4. Dump the accessory info from your Mac. If you have a Mac running MacOS 14 or under, great! Run `python3 -m findmy decrypt --out-dir devices/`. Otherwise, follow the instructions [here](https://docs.mikealmel.ooo/FindMy.py/getstarted/02-fetching.html), or use a VM running MacOS 14 or under (i.e [this one](https://github.com/sickcodes/Docker-OSX)) (may take 1-2 hours to set up) and put the `.json` files in the `devices` subdirectory. If you have other devices attached to your account that you don't want to be tracked with this API, delete the corresponding `.json` file.
5. Start the API with `flask run`.

## Environment variables
| Variable | Explanation |
|----------|-------------|
| `EMAIL`  | Email of the Apple ID the Airtags are attached to. Can be removed after you generate `account.enc` |
| `PASSWORD` | Password of the Apple ID the Airtags are attached to. Can be removed after you generate `account.enc` |
| `SECRET_KEY` | Key used to encrypt the account session |
| `API_KEY` | API key (present as a bearer token in a request's header) needed to access the API |
| `PORT` | Port that the API runs on |

## Routes

```
GET /devices
```
Returns the location of all devices and the timestamp at which each had its location was checked.

```
GET /devices/<slug>
```
Returns the location of the selected device and the timestamp at which its location was checked.

## Notes
You can rename the device's `.json` files to anything, which is recommended to make them more readable. This name is the name that is used in the API response.

Airtags all need to be attached to the same Apple account to work. This Apple Account must not have passkey authentication on. We recommend using a dummy account.

They don't need to be actual Airtags, but they do need to be compatible with the Apple Find My Network. 
