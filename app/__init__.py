# New Relic bullshit
import newrelic.agent
newrelic.agent.initialize('newrelic.ini')

from flask import Flask
from flask.ext.cache import Cache
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
from flask.ext.sqlalchemy import SQLAlchemy
from raven.contrib.flask import Sentry
import steam
# Create app
app = Flask(__name__)
app.config.from_object("settings")

# Load extensions
mem_cache = Cache(app, config=app.config["CACHE_MEMCACHED"])
fs_cache = Cache(app, config=app.config["CACHE_FS"])
db = SQLAlchemy(app)
login_manager = LoginManager(app)
oid = OpenID(app)

sentry = Sentry(app)

# Setup steamodd
steam.api.key.set(app.config['STEAM_API_KEY'])
steam.api.socket_timeout.set(5)

# Setup debugtoolbar if we're in debug mode.
if app.debug:
    from flask.ext.debugtoolbar import DebugToolbarExtension
    toolbar = DebugToolbarExtension(app)


# Set up jinja2 filters.
from app.filters import escape_every_character,\
    timestamp_to_datestring,\
    datetime_to_datestring,\
    seconds_to_time
app.add_template_filter(escape_every_character)
app.add_template_filter(timestamp_to_datestring)
app.add_template_filter(datetime_to_datestring)
app.add_template_filter(seconds_to_time)


# Load current app version into globals
from helpers import current_version
app.config['VERSION'] = current_version()

# Load views
import views

# Load blueprints
from app.users.views import mod as users_module
app.register_blueprint(users_module)


# Setup logging
import logging
app.logger.setLevel(logging.INFO)  # Set root logger to handle anything info and above

# Database logging for warnings
from app.handlers import SQLAlchemyHandler
db_handler = SQLAlchemyHandler()
db_handler.setLevel(logging.INFO)
app.logger.addHandler(db_handler)
