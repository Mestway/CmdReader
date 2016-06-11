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

class App(object):

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def service(self):
        return {"hi": "bye"}

    @cherrypy.expose
    def index(self):
        return cherrypy.lib.static.serve_file(os.path.join(ROOT, "index.html"))

if __name__ == "__main__":
    cherrypy.quickstart(App(), config=config)
