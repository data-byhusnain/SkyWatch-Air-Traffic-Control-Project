# ============================================================
# app/api/__init__.py — REST API Blueprint Registration
# ============================================================
#
# PURPOSE:
#   Turns the api/ folder into a Flask Blueprint.
#   A Blueprint is Flask's way of grouping related routes together
#   so they can be registered on the app as a unit.
#
# HOW IT CONNECTS:
#   app/__init__.py calls: app.register_blueprint(api_blueprint)
#   All routes defined in routes.py become accessible under /api/
# ============================================================

from flask import Blueprint

# Create the blueprint instance.
# url_prefix='/api' means every route in routes.py is prefixed with /api
# e.g. @api_blueprint.route('/status') becomes GET /api/status
api_blueprint = Blueprint("api", __name__, url_prefix="/api")

# Import routes AFTER creating the blueprint to avoid circular imports.
# This registers the route decorators onto api_blueprint.
from app.api import routes  # noqa: E402, F401
