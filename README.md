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

Finally you will need to configure a few server parameters:

    $ cp site_config.py.sample site_config.py

Then modify `site_config.py` appropriately.

### Run

    $ python src/server.py

Stop the server with Ctrl+C.

The server accepts a number of command-line arguments for deployment; for help,
run

    $ python src/server.py --help

Important pages:

 - `/`: main entry point for users to start collecting data pairs
 - `/status`: server and data collection status info

### User Administration

    $ python src/remove_user_trace.py user_id option
    
Removes the specified type of trace of a particular user.

    $ python src/remove_user_annotation.py user_id url
    
Removes a specific user's annotation on a specific url.
