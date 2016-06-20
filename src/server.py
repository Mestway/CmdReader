#!/usr/bin/env python

import functools
import json
import os
import cherrypy
from apiclient.discovery import build
import apiclient.errors as errors
from db import DBConnection

# Root location where we can find resource files.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Create sessions folder if it is missing
try:
    os.makedirs(os.path.join(ROOT, "sessions"))
except Exception as e:
    pass # no problem!

config = {
    "/": {
        "tools.sessions.on": True,
        "tools.sessions.storage_type": "file",
        "tools.sessions.storage_path": os.path.join(ROOT, "sessions"),
        "tools.sessions.timeout": 60 }, # in minutes
    "/search.html": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "search.html")
    },
    "/collect_page.html": {
        "tools.staticfile.on": True,
        "tools.staticfile.filename": os.path.join(ROOT, "collect_page.html") },
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
}

def search(phrase):
    service = build("customsearch", "v1",
                    developerKey="AIzaSyA049kTJjSL8DotsLVf4rSKdc0wuVrsV0M")
    Search_Engine_ID = "001089351014153505670:7jbzwugbvrc"

    numResults = 10         # TODO: decide this number later based on user experience
    limit = 10              # maximum number of search results returned per query

    urls = []
    try:
        for i in xrange(numResults / limit):
            res = service.cse().list(
                q=phrase.decode('utf-8'),
                cx=Search_Engine_ID,
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

def check_type(value, ty, value_name="value"):
    """
    Verify that the given value has the given type.
        value      - the value to check
        ty         - the type to check for
        value_name - the name to print for debugging

    The type ty can be:
        str, int, float, or bytes - value must have this type
        [ty]                      - value must be a list of ty
        {k:ty,...}                - value must be a dict with keys of the given types
    """

    if ty in [str, int, float, bytes]:
        assert type(value) is ty, "{} has type {}, not {}".format(value_name, type(value), ty)
    elif type(ty) is list:
        assert type(value) is list, "{} has type {}, not {}".format(value_name, type(value), dict)
        for i in range(len(value)):
            check_type(value[i], ty[0], "{}[{}]".format(value_name, i))
    elif type(ty) is dict:
        assert type(value) is dict, "{} has type {}, not {}".format(value_name, type(value), dict)
        for k, t in ty.items():
            assert k in value, "{} is missing key {}".format(value_name, repr(k))
            check_type(value[k], t, "{}[{}]".format(value_name, repr(k)))
    else:
        raise Exception("unknown type spec {}".format(repr(ty)))

def user_id_required(f):
    @functools.wraps(f)
    def g(*args, **kwargs):
        user_id = cherrypy.session.get("user_id")
        if user_id is None:
            raise Exception("no user id!")
        return f(*args, user_id=user_id, **kwargs)
    return g

def is_admin(username, password):
    # TODO: real auth
    return username == "admin" and password == "admin"

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
    def get_search_phrase(self, user_id):
        return self.search_phrase;

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def pick_url(self, user_id, search_phrase=None):
        self.search_phrase = search_phrase
        with DBConnection() as db:
            # save search results
            if search_phrase and not db.already_searched(search_phrase):
                db.add_urls(search_phrase, search(search_phrase))
            return db.lease_url(user_id=user_id)

    @cherrypy.expose
    @user_id_required
    @cherrypy.tools.json_out()
    def add_pairs(self, user_id, pairs):
        pairs = json.loads(pairs)
        check_type(pairs, [{"url":str, "nl":str, "cmd":str}], value_name="pairs")
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
            for url, _ in db.find_urls_with_less_responses_than():
                res += url + "<br>"

            res += "<h3>Pairs</h3>"
            res += "<table><thead><tr><th>user</th><th>url</th><th>nl</th><th>cmd</th></tr></thead><tbody>"
            for url, user, nl, cmd in db.pairs():
                res += "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(user, url, nl, cmd)
            res += "</tbody></table>"

        res += "</html>"
        return res

    @cherrypy.expose
    def index(self):
        return cherrypy.lib.static.serve_file(os.path.join(ROOT, "login.html"))

if __name__ == "__main__":
    cherrypy.quickstart(App(), config=config)