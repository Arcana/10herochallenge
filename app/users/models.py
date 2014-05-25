from app import db, steam
from app.models import Challenge
from flask.ext.login import AnonymousUserMixin
from datetime import datetime


class AnonymousUser(AnonymousUserMixin):
    def is_admin(self):
        return False

    def allows_ads(self):
        return True


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(64), unique=False, nullable=True)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.Column(db.Boolean, default=False)
    show_ads = db.Column(db.Boolean, default=True)

    logs_resolved = db.relationship('Log', backref='resolved_by_user', lazy='dynamic', cascade='all')
    challenges = db.relationship('Challenge', backref='user', lazy='dynamic', cascade="all")

    # Set default order by
    __mapper_args__ = {
        "order_by": [db.asc(first_seen)]
    }

    ACCOUNT_ID_TO_STEAM_ID_CORRECTION = 76561197960265728

    def __init__(self, _id=None, name=None, enabled=True):
        self.id = _id
        self.name = name
        self.enabled = enabled

    def __repr__(self):
        return self.name

    def get_id(self):
        return unicode(self.id)

    def is_active(self):
        return self.enabled

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def is_admin(self):
        return self.admin

    def update_last_seen(self):
        # Called every page load for current_user
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def update_steam_name(self):
        # Called every page load for current_user (API is cached)
        steam_account_info = steam.user.profile(self.steam_id)
        try:
            if steam_account_info is not None:
                if self.name is not steam_account_info.persona:
                    self.name = steam_account_info.persona
                    db.session.add(self)
                    db.session.commit()
        except steam.api.HTTPError:
            pass

    def allows_ads(self):
        return self.show_ads

    @property
    def steam_id(self):
        return self.id + User.ACCOUNT_ID_TO_STEAM_ID_CORRECTION

    def get_active_challenge(self):
        return self.challenges.filter(Challenge.start_at <= datetime.utcnow(), Challenge.end_at >= datetime.utcnow()).first()
