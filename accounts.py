import os
import webapp2
import jinja2
from google.appengine.api import users


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def expandTemplate(fileName, values):
    template = JINJA_ENVIRONMENT.get_template(fileName)
    return template.render(values)


class EditAccount(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.write(expandTemplate("edit_account.html", {
                "logout_url": users.create_logout_url(self.request.uri),
                "account": user,
            }))
        else:
            self.response.write(expandTemplate("welcome.html", {
                "login_url": users.create_login_url(self.request.uri),
            }))            


application = webapp2.WSGIApplication([
    ('/', EditAccount),
], debug=True)
