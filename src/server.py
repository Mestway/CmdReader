import cherrypy
from db import DBConnection

class App(object):
    @cherrypy.expose
    def index(self):
        with DBConnection() as db:
            out = "Hello!<br>"
            for nl, cmd in db.pairs():
                out += "Pair: {}, {}<br>".format(nl, cmd)
            return out

cherrypy.quickstart(App())
