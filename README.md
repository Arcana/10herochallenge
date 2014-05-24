10 Hero Challenge
============

## Brief:

* 10 new heroes selected at midnight GMT.
* Each win with a hero earns points.
* Global, regional (matches played in a region), and friends-list leaderboards going by total points.
* Points can be spent on re-rolling heroes.


## Requirements

* Python 2.7
* pip
* Bower
* Sass

## First run

* `git clone https://github.com/Arcana/10herochallenge.git`
* `virtualenv 10herochallenge`
* `cd 10herochallenge`
* `source bin/activate`
* `pip install -r requirements.txt`
* `bower install`
* `sass --no-cache --update ./app/static/css`
* `cp settings_example.py settings.py`
* `vim settings.py`
* `python -c "from app import db;db.create_all()"`
* `python run.py`

Easy life.


## License

Undecided.  For now just assume the license is a 10ft 1000lbs giant with an anger problem - if you do anything remotely controversial he will eat you.
