from flask import Flask, make_response
from cassandra.cluster import Cluster
from .persistence_module import Persistence
from flask_cors import CORS
from flask_selfdoc import Autodoc
from cassandra.auth import PlainTextAuthProvider
import os

server_unavailable = False

app = Flask("CJA API")
auto = Autodoc(app)
CORS(app, resources={r"/api/*": {"origins": "*"}}, vary_header=False)

db = Persistence().create_schema()

from app.center_module.center_controller import centers_controller
from app.calibration_module.calibration_controller import calibration_controller

# from app.highlights_module.controller import hightlights_controller
from app.timeline_module.timeline_controller import timeline_controller
from app.user_module.user_controller import users_controller

app.register_blueprint(centers_controller)
app.register_blueprint(calibration_controller)
# app.register_blueprint(hightlights_controller)
app.register_blueprint(timeline_controller)
app.register_blueprint(users_controller)


@app.route("/documentation")
def documentation():
    return auto.html()


@app.route("/status")
def health_check():
    try:
        db.connection.execute("SELECT now() from cja_data.center;")
        return make_response({"status": "OK"}, 200)
    except Exception as e:
        return make_response({"status": "Server Unavailable", "exception": str(e)}, 503)

