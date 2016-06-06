import cherrypy

class App(object):
    @cherrypy.expose
    def index(self):
        return "Hello World!"

cherrypy.quickstart(App())
