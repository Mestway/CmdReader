#!/usr/bin/env python

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
                db.add_urls(search_phrase, list(search(search_phrase)))
            return db.lease_url(user_id=1)

    @cherrypy.expose
    def index(self):
        return cherrypy.lib.static.serve_file(os.path.join(ROOT, "index.html"))

if __name__ == "__main__":
    cherrypy.quickstart(App(), config=config)
