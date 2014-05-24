from flask import render_template
from app import app, db
from flask.ext.login import current_user


# Routes
@app.route('/')
def index():
    return render_template("index.html")


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
