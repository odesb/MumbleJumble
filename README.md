# MumbleJumble

Mumble Bot based on [azlux/pymumble](https://github.com/azlux/pymumble). Check back later.

# Installation
Linux:
Install the Python 2.7 interpreter and pip through your package manager if you don't have it.

Change directory to the desired download directory, clone the repository and install the dependencies:
```bash
git clone --recursive https://github.com/xisbroken/MumbleJumble

# Install pymumble and MumbleJumble dependencies
sudo pip2 install opuslib protobuf

# Install ffmpeg through your package manager, in this case APT (Debian and Ubuntu derivatives)
sudo apt-get install ffmpeg
```
For the Youtube-dl module:
```bash
sudo apt-get install youtube-dl
```
For the ImageDownload module:
```bash
sudo pip2 install bs4 requests python-magic
```

#Quick usage
Change directory to the MumbleJumble directory:
```bash
cd MumbleJumble
```
Run the script with the following command line arguments:
```bash
    --server    Mumble server address
    --port      Mumble server port
    --user      Mumble bot username
    --password  Mumble server password
    --certfile  Mumble certification
    --reconnect Bot reconnects to the server if disconnected
    --debug     Debug=True will generate a lot of stdout messages
```
Example:
```bash
./MumbleJumble.py --server nsa.gov --port 4445 --user 'Shrek'
```

#Configuration
MumbleJumble features config.json, a configuration file that MumbleJumble falls back to when no command-line arguments are specified

#Creating modules
Creating modules for MumbleJumble has been easy and painless. Check back later for a link to a quick tutorial.

#Known bugs
- The bot sometimes stutters massively and becomes non-responsive, currently looking into it
