#!/usr/bin/env python

import json
import os
import cherrypy
from db import DBConnection

# Root location where we can find resource files.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

config = {
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
    for i in range(1,4):
        yield "url {} for phrase {}".format(i, phrase)

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

class App(object):

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def service(self):
        return {"hi": "bye"}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def pick_url(self, search_phrase=None):
        with DBConnection() as db:
            if search_phrase and not db.already_searched(search_phrase):
                db.add_urls(search_phrase, search(search_phrase))
            return db.lease_url(user_id=1)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def add_pairs(self, pairs):
        pairs = json.loads(pairs)
        check_type(pairs, [{"url":str, "nl":str, "cmd":str}], value_name="pairs")
        with DBConnection() as db:
            db.add_pairs(user_id=1, pairs=pairs)
            return True

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def no_pairs(self, url):
        with DBConnection() as db:
            db.mark_has_no_pairs(user_id=1, url=url)
            return True

    @cherrypy.expose
    def index(self):
        return cherrypy.lib.static.serve_file(os.path.join(ROOT, "index.html"))

if __name__ == "__main__":
    cherrypy.quickstart(App(), config=config)
