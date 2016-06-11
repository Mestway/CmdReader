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
        with DBConnection() as db:
            out = "Hello!<br>"
            for nl, cmd in db.pairs():
                out += "Pair: {}, {}<br>".format(nl, cmd)
            return out

if __name__ == "__main__":
    cherrypy.quickstart(App(), config=config)
