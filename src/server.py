#!/usr/bin/env python

# builtin
import argparse
import functools
import json
import os
import sys

# 3rd party
import cherrypy
from apiclient.discovery import build
import apiclient.errors as errors

# local
from db import DBConnection
import util

# Root location where we can find resource files.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Load local site configuration (site_config.py).
sys.path.append(ROOT)
try:
    import site_config
except ImportError as e:
    print("site_config.py was not found; see README.md")
    sys.exit(1)
for attr in ["admin_username", "admin_password", "google_api_key", "google_search_engine_id"]:
    assert hasattr(site_config, attr), "site_config.py does not declare {}".format(attr)

# Create sessions folder if it is missing
try:
    os.makedirs(os.path.join(ROOT, "sessions"))
except Exception as e:
    pass # no problem!

# CherryPy config
config = {
    "/": {
        "tools.sessions.on": True,
        "tools.sessions.storage_type": "file",
        "tools.sessions.storage_path": os.path.join(ROOT, "sessions"),
        "tools.sessions.timeout": 60 }, # in minutes
    "/search.html": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "html", "search.html")
    },
    "/collect_page.html": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "html", "collect_page.html") },
    "/cmd.ico": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "cmd.ico") },
    "/js": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": os.path.join(ROOT, "js") },
    "/css": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": os.path.join(ROOT, "css") },
    "/fonts": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": os.path.join(ROOT, "fonts") },
    "/php": {
        "tools.staticdir.on": True,
        "tools.staticdir.dir": os.path.join(ROOT, "php") },
}

def search(phrase):
    service = build("customsearch", "v1",
                    developerKey=site_config.google_api_key)

    numResults = 10         # TODO: decide this number later based on user experience
    limit = 10              # maximum number of search results returned per query

    urls = []
    try:
        for i in range(util.divide_and_round_up(numResults, limit)):
            res = service.cse().list(
                q=phrase.decode('utf-8') if type(phrase) is bytes else phrase,
                cx=site_config.google_search_engine_id,
                start=str(i*limit+1)
            ).execute()
            for result in res[u'items']:
                urls.append(result['link'])
    except errors.HttpError as err:
        print("HttpError in search(phrase): {0}".format(err))
    except:
        print("Unexpected error in search(phrase):", sys.exc_info()[0])
        raise

    return urls

def user_id_required(f):
    @functools.wraps(f)
    def g(*args, **kwargs):
        user_id = cherrypy.session.get("user_id")
        if user_id is None:
            raise Exception("no user id!")
        return f(*args, user_id=user_id, **kwargs)
    return g

def is_admin(username, password):
    return username == site_config.admin_username and password == site_config.admin_password

def parse_auth(value):
    parsed = cherrypy.lib.httpauth.parseAuthorization(value)
    return parsed.get("username"), parsed.get("password")

def admin_only(f):
    @functools.wraps(f)
    def g(*args, **kwargs):
        admin = cherrypy.session.get("admin")
        if not admin:
            if "authorization" in cherrypy.request.headers and is_admin(*parse_auth(cherrypy.request.headers["authorization"])):
                cherrypy.session["admin"] = True
            else:
                cherrypy.response.headers["WWW-Authenticate"] = 'Basic realm="User Visible Realm"'
                raise cherrypy.HTTPError(401,
                    "You are not authorized to access that resource")
        return f(*args, **kwargs)
    return g

class App(object):
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def count_current_users(self):
        with DBConnection() as db:
            return db.num_users()

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def register_user(self, user_id):
        with DBConnection() as db:
            db.register_user(user_id=user_id)
            return True

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def user_login(self, username):
        # Username format: nl2cmdXX
        user_id = int(username[6:])
        with DBConnection() as db:
            if db.user_exist(user_id):
                cherrypy.session["user_id"] = user_id
                return True
            else:
                return False
    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_current_user(self, user_id):
        print(user_id)
        return user_id;

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def logout_user(self):
        cherrypy.session["user_id"] = None
        return True

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_search_phrase(self, user_id):
        return self.search_phrase;

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def pick_url(self, user_id, search_phrase=None):
        self.search_phrase = search_phrase
        with DBConnection() as db:
            # save search results
            if search_phrase and search_phrase != "RANDOM_SELECTION":
                if not db.already_searched(search_phrase):
                    db.add_urls(search_phrase, search(search_phrase))
            return db.lease_url(user_id=user_id)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def add_pairs(self, user_id, pairs):
        pairs = json.loads(pairs)
        util.check_type(pairs, [{"url":unicode, "nl":unicode, "cmd":unicode}], value_name="pairs")
        with DBConnection() as db:
            db.add_pairs(user_id=user_id, pairs=pairs)
            return True

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def no_pairs(self, user_id, url):
        with DBConnection() as db:
            db.mark_has_no_pairs(user_id=user_id, url=url)
            return True

    @cherrypy.expose
    @admin_only
    def status(self):
        import db
        res = "<html>"

        res += "<h3>Active URL leases</h3>"
        if db.url_leases:
            res += "<table><thead><tr><th>user</th><th>url</th><th>expires</th></tr></thead><tbody>"
            for url, user, expires in db.url_leases:
                res += "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(user, url, expires)
            res += "</tbody></table>"
        else:
            res += "N/A"

        with DBConnection() as db:
            res += "<h3>URLs in queue</h3>"
            for url, _ in db.find_urls_with_less_responses_than(None):
                res += url + "<br>"

            res += "<h3>Pairs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th><th>nl</th><th>cmd</th></tr></thead><tbody>"
            for user, url, nl, cmd in db.pairs():
                res += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(user, url, nl, cmd)
            res += "</tbody></table>"

        res += "</html>"
        return res

    @cherrypy.expose
    def index(self):
        return cherrypy.lib.static.serve_file(os.path.join(ROOT, "html", "login.html"))

if __name__ == "__main__":

    # read and parse cmdline args
    parser = argparse.ArgumentParser(description="Data gathering server.")
    parser.add_argument("-H", "--host", metavar="HOST_NAME", default="127.0.0.1", help="Host interface to bind to")
    parser.add_argument("-p", "--port", metavar="PORT_NUM", default="8080", help="Port to run on")
    args = parser.parse_args()

    # Setup and start CherryPy
    cherrypy.config.update({
        "server.socket_host": args.host,
        "server.socket_port": int(args.port) })
    cherrypy.quickstart(App(), config=config)
