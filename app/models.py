from app import db, fs_cache, steam
from flask import current_app
from datetime import datetime
from random import sample

class Log(db.Model):
    """ Model used for logging to database. """
    __tablename__ = 'logs'

    id = db.Column(db.Integer, primary_key=True)  # auto incrementing
    logger = db.Column(db.String(64))  # the name of the logger. (e.g. myapp.views)
    level = db.Column(db.String(16))  # info, debug, or error?
    trace = db.Column(db.Text)  # the full traceback printout
    msg = db.Column(db.Text)  # any custom log you may have included
    extra = db.Column(db.Text)  # Any extra data given
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # the current timestamp
    resolved_by_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(created_at)]
    }

    def __init__(self, logger=None, level=None, trace=None, msg=None, extra=None):
        self.logger = logger
        self.level = level
        self.trace = trace
        self.msg = msg
        self.extra = extra

    def __unicode__(self):
        return self.__repr__()

    def __repr__(self):
        return "<Log: %s - %s>" % (self.created_at.strftime('%m/%d/%Y-%H:%M:%S'), self.msg[:50])

    def resolve(self, user_id):
        """ Mark this log as resolved / at least acknowledge it's been seen. """
        if not self.resolved:
            self.resolved_by_user_id = user_id
            self.resolved_at = datetime.utcnow()

    @property
    def resolved(self):
        """ Returns whether this log has been resolved or not. """
        return self.resolved_by_user_id is not None


class Challenge(db.Model):
    __tablename__ = 'challenges'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    start_at = db.Column(db.DateTime)
    end_at = db.Column(db.DateTime)

    heroes = db.relationship('ChallengeHero', backref='challenge', lazy='joined')

    def __init__(self, user_id, start_at=None, end_at=None, generate_heroes=True):
        if not start_at:
            # Default to midnight
            start_at = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        if not end_at:
            # Default to just before midnight
            end_at = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999)

        self.user_id = user_id
        self.start_at = start_at
        self.end_at = end_at

        if generate_heroes:
            db.session.add(self)
            db.session.flush()
            self._generate_heroes()

    def _generate_heroes(self):
        chosen_ones = sample(Hero.query.all(), current_app.config['CHALLENGE_HERO_COUNT'])

        for chosen_one in chosen_ones:
            challenge_hero = ChallengeHero(self.id, chosen_one.id)
            db.session.add(challenge_hero)  # Add to session but don't commit - that'll be handled elsewhere.


    def get_completed_heroes(self):
        """ Returns heroes which have been completed. """
        return [h for h in self.heroes if h.completed]

    def get_outstanding_heroes(self):
        """ Returns heroes which are yet to be completed. """
        return [h for h in self.heroes if h.active and not h.completed]

    def get_rerolled_heroes(self):
        """ Returns heroes which were selected via a re-roll """
        return [h for h in self.heroes if h.rerolled]

    def get_active_heroes(self):
        """ Returns the full-list of this challenge's active heroes (complete and incomplete) """
        return [h for h in self.heroes if h.active]


class ChallengeHero(db.Model):
    """ A join-table between a Challenge and its heroes """
    __tablename__ = 'challenge_heroes'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    challenge_id = db.Column(db.Integer, db.ForeignKey("challenges.id"))
    hero_id = db.Column(db.Integer, db.ForeignKey("heroes.id"))
    hero = db.relationship("Hero", lazy="joined")

    active = db.Column(db.Boolean, default=True)  # Whether this ChallengeHero counts toward the challenge (false if it was not completed at time of re-roll)
    rerolled = db.Column(db.Boolean)  # Whether this ChallengeHero was selected via re-roll
    completed = db.Column(db.Boolean)

    def __init__(self, challenge_id=None, hero_id=None, rerolled=False, completed=False):
        self.challenge_id = challenge_id
        self.hero_id = hero_id
        self.rerolled = rerolled
        self.completed = completed


class Hero(db.Model):
    """ Represents a Dota 2 hero. """
    __tablename__ = 'heroes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=False)  # We'll set this from WebAPI data
    name = db.Column(db.String(80))
    localized_name = db.Column(db.String(80), nullable=True)

    def __init__(self, _id, name, localized_name=None):
        self.id = _id
        self.name = name
        self.localized_name = localized_name

    @property
    def image(self):
        return "http://media.steampowered.com/apps/dota2/images/heroes/{}_full.png".format(self.name.replace('npc_dota_hero_', ''))

    @classmethod
    @fs_cache.cached(timeout=60 * 60, key_prefix="heroes")
    def fetch_heroes_from_webapi(cls):
        """ Fetch a list of heroes from the Dota 2 WebAPI.

        Uses steamodd to interface with the WebAPI.  Falls back to data stored on the file-system in case of a HTTPError
        when interfacing with the WebAPI.

        Returns:
            An array of Hero objects.
        """
        try:
            res = steam.api.interface("IEconDOTA2_570").GetHeroes(language="en_US").get("result")
            return res.get("heroes")

        except steam.api.HTTPError:
            current_app.logger.warning('Hero.get_all returned with HTTPError', exc_info=True)
            return list()

    @classmethod
    def update_heroes_from_webapi(cls):
        """ Loops over heroes from WebAPI updating or inserting new data where appropriate. """
        for webapi_hero in cls.fetch_heroes_from_webapi():
            # Check if we have a hero entry
            hero = cls.query.filter(cls.id == webapi_hero.get('id')).first()

            # If we don't have a hero entry, make a new one
            if not hero:
                hero = cls(
                    webapi_hero.get('id'),
                    webapi_hero.get('name'),
                    webapi_hero.get('localized_name'),
                )

            # Update hero entry's deets
            hero.name = webapi_hero.get('name')
            hero.localized_name = webapi_hero.get('localized_name')

            # Tell database we want to save it
            db.session.add(hero)

        # Commit all changes to database
        db.session.commit()
