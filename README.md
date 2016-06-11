# CmdReader

### Setup

First, install the Python packages we need:

    $ sudo pip install -r requirements.txt

If you don't have write permission to your system's Python package folder, you
might want to instead:

    $ pip install --user -r requirements.txt

In either case, you might prefer to run the server from a virtual environment:

    $ virtualenv envdir
    $ . envdir/bin/activate
    $ pip install -r requirements.txt
    
### Install Google Search API

    $ pip install [--user] google-api-python-client

### Run

    $ python src/server.py

Stop the server with Ctrl+C.

Important pages:

 - `/`: main entry point for users to start collecting data pairs
 - `/status`: server and data collection status info
