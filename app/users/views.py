from flask import Blueprint, render_template, flash, redirect, request, url_for, current_app

from app import app, oid, steam, db, login_manager, mem_cache
from models import User, AnonymousUser
from forms import SettingsForm
from flask.ext.login import login_user, logout_user, current_user, login_required

mod = Blueprint("users", __name__, url_prefix="/users")

login_manager.anonymous_user = AnonymousUser


# User authentication
@login_manager.user_loader
def load_user(user_id):
    _user = User.query.get(user_id)

    _update_name_updated_key = 'update_name_for_user_{}_updated'.format(user_id)
    _update_name_lock_key = 'update_name_for_user_{}_lock'.format(user_id)

    if _user:
        _user.update_last_seen()

        if not mem_cache.get(_update_name_updated_key) and not mem_cache.get(_update_name_lock_key):
            # Set lock befoer doing slow task
            mem_cache.set(_update_name_lock_key, True, timeout=app.config['UPDATE_USER_NAME_TIMEOUT'])

            # Update user's name
            _user.update_steam_name()

            # Set key to say we've updated the name.  We'll re-run this when this key expires
            mem_cache.set(_update_name_updated_key, True, timeout=app.config['UPDATE_USER_NAME_TIMEOUT'])

            # Release lock
            mem_cache.delete(_update_name_lock_key)

    return _user


@mod.route('/login/')
@oid.loginhandler
def login():
    if current_user.is_authenticated():
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')


@oid.after_login
def create_or_login(resp):
    steam_id = long(resp.identity_url.replace("http://steamcommunity.com/openid/id/", ""))
    account_id = int(steam_id & 0xFFFFFFFF)
    _user = User.query.filter(User.id == int(account_id & 0xFFFFFFFF)).first()

    if not _user:
        _user = User(int(account_id & 0xFFFFFFFF), steam.user.profile(steam_id).persona or account_id)

        db.session.add(_user)
        db.session.commit()

    login_attempt = login_user(_user)
    if login_attempt is True:
        flash(u"You are logged in as {}".format(_user.name), "success")
    elif not _user.is_active():
        flash(u"Cannot log you in as {}, your account has been disabled.  If you believe this is in error, please contact {}.".format(_user.name, current_app.config["CONTACT_EMAIL"]), "danger")
    else:
        flash(u"Error logging you in as {}, please try again later.".format(_user.name), "danger")
    return redirect(oid.get_next_url())


@mod.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(oid.get_next_url())


@mod.route("/")
@mod.route("/page/<int:page>/")
def users(page=1):
    if not current_user.is_admin():
        flash("User list is admin only atm.", "danger")
        return redirect(request.referrer or url_for("index"))
    _users = User.query.paginate(page, current_app.config["USERS_PER_PAGE"], False)
    return render_template("users/users.html",
                           title="Users - 10 Hero Challenge",
                           users=_users)


@mod.route("/<int:_id>/")
def user(_id):
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    challenges = _user.challenges

    return render_template("users/user.html",
                           title=u"{} - 10 Hero Challenge".format(_user.name),
                           user=_user,
                           challenges=challenges)


@mod.route("/<int:_id>/update_name")
@login_required
def update_name(_id):
    # Check auth
    if not current_user.is_admin():
        flash("Only admins can force-update user names.", "danger")
        return redirect(request.referrer or url_for("index"))

    # Get user
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    old_name = _user.name
    _user.update_steam_name()
    new_name = _user.name

    current_app.logger.info("Manually triggered a user name update.", extra={
        'extra': {
            'old_name': old_name,
            'new_name': new_name,
            'actioned_by': current_user.id
        }
    })

    flash(u"Updated user {}'s name from {} to {}.".format(_id, old_name, new_name), "success")
    return redirect(request.referrer or url_for("index"))


@mod.route("/<int:_id>/settings/", methods=["POST", "GET"])
@login_required
def settings(_id):
    # Authentication
    if current_user.id != _id and not current_user.is_admin():
        flash("You are not authorised to edit user {}'s settings.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    # Check user exists
    _user = User.query.filter(User.id == _id).first()
    if _user is None:
        flash("User {} not found.".format(_id), "danger")
        return redirect(request.referrer or url_for("index"))

    # Validate form, if submitted; else render it.
    form = SettingsForm(_user, request.form)

    if form.validate_on_submit():
        _user.email = form.email.data
        _user.show_ads = form.show_ads.data
        db.session.add(_user)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("users.user", _id=_user.id))

    return render_template("users/settings.html",
                           title="Your settings - 10 Hero Challenge",
                           user=_user,
                           form=form)
