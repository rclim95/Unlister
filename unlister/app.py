"""The module that contains the Flask app for Unlister"""

from flask import Blueprint, render_template

bp = Blueprint("app", __name__)

@bp.get("/")
def index():
    """The homepage."""
    return render_template("app/index.html")
