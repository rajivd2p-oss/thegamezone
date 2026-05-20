# thegamezone

Airtag tracker + web API. Made for Hack Club the Game, a 100 player Jet Lag inspired adventure across Manhattan.

## Usage
1. Install dependencies with `python3 pip install -r requirements.txt` (in a virtual environment, you get the deal)
2. Fill out `EMAIL` and `PASSWORD` in `.env`, as well as a randomly generated string for `API_KEY` and `SECRET_KEY`. You can remove `EMAIL` and `PASSWORD` after you complete Step 3.
3. Generate your encoded account session using `python3 account.py`.
4. Dump the accessory info from your Mac. If you have a Mac running MacOS 14 or under, great! Run `python3 -m findmy decrypt --out-dir devices/`. Otherwise, follow the instructions [here](https://docs.mikealmel.ooo/FindMy.py/getstarted/02-fetching.html), or use a VM running MacOS 14 or under (i.e [this one](https://github.com/sickcodes/Docker-OSX)) (may take 1-2 hours to set up) and put the `.json` files in the `devices` subdirectory. If you have other devices attached to your account that you don't want to be tracked with this API, delete the corresponding `.json` file. Alternatively, upload device files to a running instance via `POST /devices` or `python3 upload.py`.
5. Start the API with `flask run`.

## Development mode

Set `DEV_MODE=true` to run without Apple credentials. All location endpoints return randomized, plausible coordinates inside Manhattan that drift slightly on each request. No `account.enc`, `ani_libs.bin`, or device `.json` files are required — the POST `/devices` endpoint registers devices in-memory only.

```bash
DEV_MODE=true API_KEY=dev flask run
```

## Environment variables
| Variable | Explanation |
|----------|-------------|
| `EMAIL`  | Email of the Apple ID the Airtags are attached to. Can be removed after you generate `account.enc` |
| `PASSWORD` | Password of the Apple ID the Airtags are attached to. Can be removed after you generate `account.enc` |
| `SECRET_KEY` | Key used to encrypt the account session |
| `API_KEY` | API key (present as a bearer token in a request's header) needed to access the API |
| `PORT` | Port that the API runs on |
| `DEV_MODE` | Set to `true` to mock Manhattan locations without Apple credentials (default: `false`) |
| `DATA_DIR` | Directory where `account.enc` and `devices/` are stored (default: `.`) |

## Routes

```
GET /devices
```
Returns the location of all devices and the timestamp at which each had its location was checked.

```
GET /devices/<slug>
```
Returns the location of the selected device and the timestamp at which its location was checked. The slug used is the name of the corresponding `.json` file.

```
POST /devices
```
Adds a new device. Accepts two formats:

**JSON body** (`Content-Type: application/json`): post the accessory `.json` file contents directly as the request body. The slug is inferred from the `name` field inside the JSON.

**Multipart form** (`multipart/form-data`): upload the accessory `.json` as `file`. The slug is inferred from the filename.

Slugs may only contain alphanumeric characters, hyphens, and underscores. Returns the slug of the created device on success, or 409 if a device with that slug already exists.

To bulk-upload all files in the `devices/` directory to a remote endpoint:
```bash
python3 upload.py <endpoint> --api-key <key>
```

## Production deployment

Use a WSGI server instead of `flask run`:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:$PORT app:app
```

### Docker

A `docker-compose.yml` is provided. `account.enc` and `devices/` are stored in a named volume (`appdata`) mounted at `/app/data`, so they persist across redeploys.

On first deploy, generate `account.enc` by execing into the running container:

```bash
docker compose exec app python account.py
```

`ani_libs.bin` is downloaded automatically by the `findmy` library on first run and saved into the named volume alongside `account.enc`.


## Notes
You can rename the device's `.json` files to anything, which is recommended to make them more readable. This name is the name that is used in the API response.

Airtags all need to be attached to the same Apple account to work. This Apple Account must not have passkey authentication on. We recommend using a dummy account.

They don't need to be actual Airtags, but they do need to be compatible with the Apple Find My Network. 
