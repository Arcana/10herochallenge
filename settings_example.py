import os

APP_DIR = os.path.abspath(os.path.dirname(__file__))

STEAM_API_KEY = ""  # TODO
DEBUG = False
TESTING = False
SECRET_KEY = ""  # TODO
SQLALCHEMY_DATABASE_URI = ''  # TODO
DEBUG_TB_INTERCEPT_REDIRECTS = False

CACHE_MEMCACHED = {
    'CACHE_TYPE': "memcached",
    'CACHE_MEMCACHED_SERVERS': ["127.0.0.1:11211"],
    'CACHE_KEY_PREFIX': "10hero",
    #'CACHE_DEFAULT_TIMEOUT',
    #'CACHE_ARGS',
    #'CACHE_OPTIONS'
}

CACHE_FS = {
    'CACHE_TYPE': "filesystem",
    'CACHE_DIR': APP_DIR + os.sep + '.cache',
    #'CACHE_DEFAULT_TIMEOUT',
    #'CACHE_ARGS',
    #'CACHE_OPTIONS'
}

ENCRYPTION_KEY = ""  # 16, 24, or 32 bytes long  # TODO

# Sentry info
SENTRY_ENABLED = False
SENTRY_DSN = ""


# General vars
CONTACT_EMAIL = ""  # TODO
BITCOIN_DONATION_ADDRESS = ""  # TODO
DATE_STRING_FORMAT = "%d %b %Y, %H:%M"
USERS_PER_PAGE = 32
CHALLENGE_HERO_COUNT = 10
