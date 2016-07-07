#!/usr/bin/env python

# builtin
import argparse
import functools
import json
import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import threading

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

# Create database schema (if it does not exist)
with DBConnection() as db:
    db.create_schema()

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
    "/user_inspection.html": {
        "tools.staticfile.on":True,
        "tools.staticfile.filename": os.path.join(ROOT, "html", "user_inspection.html")
    },
    "/cmd.ico": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "cmd.ico") },
    "/wait.svg": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "wait.svg") },
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

    numResults = 50         # TODO: decide this number later based on user experience
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
            if "authorization" in cherrypy.request.headers and \
                    is_admin(*parse_auth(cherrypy.request.headers["authorization"])):
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
    def register_user(self, user_id, first_name, last_name):
        with DBConnection() as db:
            db.register_user(user_id, first_name, last_name)
            return True

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def user_login(self, username):
        if not username:
            return False
        # Username format: nl2cmdXX
        if not username.startswith("nl2cmd"):
            return False
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
        return user_id;

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_user_names(self, user_id):
        with DBConnection() as db:
            return db.get_user_names(user_id)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_user_report(self, user_id):
        with DBConnection() as db:
            return db.get_user_names(user_id), \
                   db.get_num_pairs_annotated(user_id), \
                   db.get_num_urls_annotated(user_id), \
                   db.get_num_urls_no_pairs(user_id), \
                   db.get_num_urls_skipped(user_id)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_leaderboard(self, user_id):
        with DBConnection() as db:
            return db.get_leaderboard(user_id)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_access_code(self, first_name, last_name):
        with DBConnection() as db:
            return db.get_access_code(first_name, last_name)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def more_time_on_page(self, user_id, current_url):
        with DBConnection() as db:
            db.renew_lease(user_id, current_url)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def logout_user(self, user_id, current_url=None):
        cherrypy.session["user_id"] = None
        if current_url:
            with DBConnection() as db:
                db.unlease_url(user_id, current_url)
        return True

    # --- Search ---

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_search_phrase(self, user_id):
        # return self.search_phrase;
        return ""

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def skip_url(self, user_id, url):
        with DBConnection() as db:
            db.skip_url(user_id, url)
            return True

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def pick_url(self, user_id, search_phrase=None):
        with DBConnection() as db:
            # save search results
            if search_phrase and search_phrase != "RANDOM_SELECTION":
                self.search_phrase = search_phrase
                if not db.already_searched(search_phrase):
                    url_list = search(search_phrase)
                    db.add_urls(search_phrase, url_list)
                    db.add_urls(search_phrase, [url_list[0]], True)
                    t = threading.Thread(target=self.add_urls, args=(search_phrase, url_list[1:]))
                    t.start()
            return db.lease_url(user_id=user_id)

    def add_urls(self, search_phrase, urls):
        with DBConnection() as db:
            db.add_urls(search_phrase, urls, True)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def get_url_html(self, user_id, url):
        with DBConnection() as db:
            return db.get_url_html(url)

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
    @cherrypy.tools.json_out()
    def already_searched(self, search_phrase):
        with DBConnection() as db:
            return db.already_searched(search_phrase)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def user_record(self, user_id):
        with DBConnection() as db:
            if not db.user_exist(user_id):
                return "User %s does not exist!" % user_id

            num_pairs_annotated = 0
            commands_annotated = set()
            num_urls_no_pairs = 0
            num_urls_skipped = 0

            res = "<h3>Pairs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th><th>nl</th><th>cmd</th></tr></thead><tbody>"
            for user, url, nl, cmd in db.pairs_by_user(user_id):
                url = url.decode().encode('utf-8')
                nl = nl.decode().encode('utf-8')
                cmd = cmd.decode().encode('utf-8')
                res += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                            user, url, nl, cmd)
                num_pairs_annotated += 1
                commands_annotated.add(cmd)
            res += "</tbody></table>"

            res += "<h3>NoPairs URLs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th></tr></thead><tbody>"
            for user, url in db.no_pairs_by_user(user_id):
                url = url.decode().encode('utf-8')
                res += "<tr><td>{}</td><td>{}</td></tr>".format(
                        user, url)
                num_urls_no_pairs += 1
            res += "</tbody></table>"

            res += "<h3>Skipped URLs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th></tr></thead><tbody>"
            for user, url in db.skipped_by_user(user_id):
                url = url.decode().encode('utf-8')
                res += "<tr><td>{}</td><td>{}</td></tr>".format(
                        user, url)
                num_urls_skipped += 1
            res += "</tbody></table>"

            stats = "<h3>" + db.get_user_names(user_id) + "</h3><br>"
            stats += "<h3>Statistics</h3>"
            stats += "num pairs annoated:\t%d" % num_pairs_annotated + "<br>"
            stats += "num unique commands annotated:\t%d" % len(commands_annotated) + "<br>"
            stats += "num urls annoated:\t%d" % db.get_num_urls_annotated(user_id) + "<br>"
            stats += "num urls no pairs:\t%d" % num_urls_no_pairs + "<br>"
            stats += "num urls skipped:\t%d" % num_urls_skipped + "<br>"

            return stats + res

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
            res += "<h3>Commands collected</h3>"
            pairs = []
            cmds = []
            for _, _, nl, cmd in db.pairs():
                pairs.append((nl, cmd))
            for cmd in db.commands():
                if not "find" in cmd:
                    cmds.append(cmd)
            res += "{} pairs <br>".format(len(pairs))
            res += "{} unique commands <br>".format(len(cmds))
            for cmd, in sorted(cmds):
                res += cmd + "<br>"

            """res += "<h3>URLs in queue</h3>"
            for url, _ in db.find_urls_with_less_responses_than(None):
                res += url + "<br>"
            """

            res += "<h3>URLs Finished</h3>"
            for url, _ in db.find_urls_that_is_done():
                res += url + "<br>"

            """res += "<h3>Pairs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th><th>nl</th><th>cmd</th></tr></thead><tbody>"
            for user, url, nl, cmd in db.pairs():
                url = url.decode().encode('utf-8')
                nl = nl.decode().encode('utf-8')
                cmd = cmd.decode().encode('utf-8')
                res += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                        user, url, nl, cmd)
            res += "</tbody></table>"
            """

            """res += "<h3>NoPairs URLs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th></tr></thead><tbody>"
            for user, url in db.nopairs():
                url = url.decode().encode('utf-8')
                res += "<tr><td>{}</td><td>{}</td></tr>".format(
                        user, url)
            res += "</tbody></table>"
            """

            """res += "<h3>Skipped URLs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th></tr></thead><tbody>"
            for user, url in db.skipped():
                url = url.decode().encode('utf-8')
                res += "<tr><td>{}</td><td>{}</td></tr>".format(
                        user, url)
            res += "</tbody></table>"
            """

            res += "<h3>Search Content</h3>"
            res += "<table><thead><tr><th>url</th><th>fingerprint</th><th>minimum distance</th><th>number of commands</th></tr></thead><tbody>"
            for url, fingerprint, min_distance, num_cmds in db.search_content():
                res += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(url, fingerprint, min_distance, num_cmds)
            res += "</tbody></table>"

            res += "<h3>Registered Users</h3>"
            res += "<table><thead><tr><th>user</th><th>first name</th><th>last name</th></tr></thead><tbody>"
            for user, fname, lname in db.users():
                res += "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(user, fname, lname)
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
