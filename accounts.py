import os
import webapp2
import jinja2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def expandTemplate(fileName, values):
    template = JINJA_ENVIRONMENT.get_template(fileName)
    return template.render(values)


class EditAccount(webapp2.RequestHandler):
    def get(self):
        self.response.write(expandTemplate("edit_account.html", dict()))


application = webapp2.WSGIApplication([
    ('/', EditAccount),
], debug=True)
