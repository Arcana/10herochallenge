from app import db
from datetime import datetime


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
