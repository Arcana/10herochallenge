from flask import render_template
from app import app, db, mem_cache
from app.models import Challenge, ChallengeHero, Hero
from app.users.models import User
from flask.ext.login import current_user
from random import sample

from datetime import datetime, timedelta

@app.before_request
def update_heroes():
    hero_info_updated = mem_cache.get('hero_info_updated')
    if not hero_info_updated:
        Hero.update_heroes_from_webapi()
        mem_cache.set('hero_info_updated', True, timeout=60*60)  # 1 hour timeout


# Routes
@app.route('/')
def index():
    current_challenge = None
    random_heroes = None

    # If authed, get or create challenge
    if current_user.is_authenticated():
        current_challenge = current_user.get_active_challenge()

        if not current_challenge:
            current_challenge = Challenge(current_user.id)
            db.session.add(current_challenge)
            db.session.commit()
    # If not authed, get 10 random hiroshimas
    else:
        random_heroes = []
        for hero in sample(Hero.query.all(), app.config['CHALLENGE_HERO_COUNT']):
            mock_challenge_hero = ChallengeHero()
            mock_challenge_hero.hero = hero
            random_heroes.append(mock_challenge_hero)

    return render_template(
        "index.html",
        current_challenge=current_challenge,
        random_heroes=random_heroes
    )


@app.route('/leaderboard')
def leaderboard():
    """ Global leader board.  Going by ChallengeHeroes completed in last 30 days for now. """

    winners = db.session.query(db.func.count(ChallengeHero), User).\
        filter(ChallengeHero.completed == True,
               Challenge.start_at >= (datetime.now() - timedelta(days=30))).\
        join(ChallengeHero.challenge).\
        join(Challenge.user).\
        order_by(db.func.count(ChallengeHero).desc()).\
        group_by(Challenge.user_id).\
        all()

    return render_template(
        "leaderboard.html",
        winners=winners
    )


@app.errorhandler(401)  # Unauthorized
@app.errorhandler(403)  # Forbidden
@app.errorhandler(404)  # > Missing middle!
@app.errorhandler(500)  # Internal server error.
# @app.errorhandler(Exception)  # Internal server error.
def internalerror(error):
    """ Custom error page, will catch 401, 403, 404, and 500, and output a friendly error message. """
    try:
        if error.code == 401:
            error.description = "I'm sorry Dave, I'm afraid I can't do that.  Try logging in."
        elif error.code == 403:
            if current_user.is_authenticated():
                error.description = "I'm sorry {{ current_user.name }}, I'm afraid I can't do that.  You do not have access to this resource.</p>"
            else:
                # Shouldn't output 403 unless the user is logged in.
                error.description = "Hacker."
    except AttributeError:
        # Rollback the session
        db.session.rollback()

        # E500's don't populate the error object, so we do that here.
        error.code = 500
        error.name = "Internal Server Error"
        error.description = "Whoops! Something went wrong server-side.  Details of the problem has been sent to our developers for investigation."

    # Render the custom error page.
    return render_template("error.html", error=error, title=error.name), error.code
