from flask.ext.wtf import Form
from flask.ext.login import current_user

from wtforms import TextField, BooleanField
from wtforms.validators import Email, Optional, ValidationError

from app.users.models import User


class SettingsForm(Form):
    email = TextField("E-mail address",
                      validators=[Optional(), Email()],
                      description="Not used for anything.")
    show_ads = BooleanField("Show ads", description="Uncheck to hide advertisements.")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(SettingsForm, self).__init__(*args, **kwargs)

    @staticmethod
    def validate_name(field):
        user = User.query.filter_by(name=field.data).first()
        if user and user.id != current_user.id:
            raise ValidationError("This username is taken")
