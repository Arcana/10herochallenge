"""

For each active challenge (and inactive - within a few hours tollerance), fetch the user's matches since
challenge.start_at minus an hour or so (volvo) until challenge.end_at plus an hour or so (volvo).

For each match, check if the user's hero is one of our challenge's active heroes, and check if the match was a win.  If
yes: Save that particular ChallengeHero as complete. (TODO: Handle re-rolls properly - we should not count hero wins before
re-roll was done (should we?)
"""

from app import steam, db
from app.models import Challenge, ChallengeHero
from datetime import datetime, timedelta
from calendar import timegm as to_timestamp

import gevent


def handle_challenge(challenge):
    webapi_params = {
        "account_id": challenge.user_id,
        "date_min": to_timestamp((challenge.start_at - timedelta(hours=2)).utctimetuple()),
        "date_max": to_timestamp((challenge.end_at + timedelta(hours=2)).utctimetuple()),
        "matches_requested": 100  # 100 Max
    }

    matches = steam.api.interface("IDOTA2Match_570").GetMatchHistory(**webapi_params).get("result")
    return_challenge_heroes = []

    print "Found {} matches for {}".format(len(matches.get("matches")), challenge.user_id)
    for match in matches.get("matches"):
        # Check match was played within the challenge dates
        start_time = datetime.fromtimestamp(match.get('start_time'))
        if not challenge.start_at <= start_time <= challenge.end_at:
            print "Match {} was not played within the challenge's timeframe".format(match.get('match_id'))
            continue

        # Get users hero
        users_hero = None
        player_was_radiant = None
        for player in match.get("players"):
            if challenge.user_id == player.get("account_id"):
                users_hero = player.get("hero_id")
                player_was_radiant = player.get('player_slot') < 128

        if not users_hero:
            print "Can't find users hero for match {}. wtf?".format(match.get('match_id'))
            continue

        # Check if user was playing a challenge hero, if so get it.
        challenge_hero = None
        for hero in challenge.get_active_heroes():
            if hero.hero_id == int(users_hero):
                challenge_hero = hero

        if not challenge_hero:
            print "User was not playing a challenge hero in match {}".format(match.get('match_id'))
            continue

        # Check if the match was winnered
        match_details = steam.api.interface("IDOTA2Match_570").GetMatchDetails(match_id=match.get('match_id')).get("result")
        if (match_details.get('radiant_win') and player_was_radiant) or \
                (not match_details.get('radiant_win') and not player_was_radiant):
            print "User won game as challenge hero in match {}.".format(match.get('match_id'))
            return_challenge_heroes.append(challenge_hero.id)
        else:
            print "User lost game as challenge hero in match {}.".format(match.get('match_id'))

    # Return this challenge's data
    return return_challenge_heroes


def check_challenges():
    """ Get a list of challenges, then spawn gevent threads for all of them. :) """
    # Get challenges that did not end 23:00 yesterday (so yesterday's and todays)
    end_before = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(hours=1)
    challenges = Challenge.query.filter(Challenge.end_at >= end_before).all()

    print "Found {} challenges to check".format(len(challenges))
    jobs = [gevent.spawn(handle_challenge, challenge) for challenge in challenges]

    gevent.wait(jobs)

    for hero in ChallengeHero.query.filter(ChallengeHero in [ch for ch in [j.value for j in jobs]]).all():
        hero.completed = True
        db.session.add(hero)
    db.session.commit()
