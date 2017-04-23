from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import cgi
import jinja2
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Restaurant, Base, MenuItem

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

class Handler(BaseHTTPRequestHandler):
    def write(self, *a, **kw):
        self.wfile.write(*a, **kw)

    def render_str(self, template, **kw):
        t=jinja_env.get_template(template)
        return t.render(kw)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class WebServerHandler(Handler):
    def do_GET(self):
        try:
            if self.path.endswith('/restaurants'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                restaurants = session.query(Restaurant).all()
                self.render('restaurants.html', restaurants=restaurants)
                return
            if self.path.endswith('/restaurants/new'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.render('newrestaurant.html')
                return
            if self.path.endswith('/edit'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                rest_id = self.path.split("/")[2]
                rest = session.query(Restaurant).filter_by(id = rest_id).one()
                if rest:
                    self.render('editrestaurant.html', rest=rest)
                return
            if self.path.endswith('/delete'):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                rest_id = self.path.split("/")[2]
                rest = session.query(Restaurant).filter_by(id = rest_id).one()
                if rest:
                    self.render('deleterestaurant.html', rest=rest)
                return

        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        try:
            if self.path.endswith('/restaurants/new'):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    rest_name = fields.get('rest_name')
                new_rest = Restaurant(name=rest_name[0])
                session.add(new_rest)
                session.commit()

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()
                return
            if self.path.endswith('/edit'):
                ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
                if ctype == 'multipart/form-data':
                    fields = cgi.parse_multipart(self.rfile, pdict)
                    new_rest_name = fields.get('new_rest_name')
                rest_id = self.path.split("/")[2]
                rest = session.query(Restaurant).filter_by(id=rest_id).one()
                if rest != []:
                    rest.name = new_rest_name[0]
                    session.add(rest)
                    session.commit()

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()
            if self.path.endswith('/delete'):
                rest_id = self.path.split("/")[2]
                rest = session.query(Restaurant).filter_by(id=rest_id).one()
                if rest != []:
                    session.delete(rest)
                    session.commit()

                self.send_response(301)
                self.send_header('Content-type', 'text/html')
                self.send_header('Location', '/restaurants')
                self.end_headers()
        except:
            pass


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print "Web Server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print " ^C entered, stopping web server...."
        server.socket.close()

if __name__ == '__main__':
    main()