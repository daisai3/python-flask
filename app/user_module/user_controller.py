from flask import Blueprint, request, jsonify, abort, make_response
from .user_facade import UserFacade
from app.auth_tools import (
    encode_auth_token,
    protected_endpoint,
    decode_auth_token,
    active_tokens,
)
import hashlib
from app import auto
from app.utils import (
    EMPTY_REQUEST,
    INVALID_FORMAT,
    INVALID_TIME_RANGES,
    NULL_PARAMS,
    CENTER_NOT_FOUND,
    USER_OR_PASSWORD_INCORRECT,
)

users_controller = Blueprint("users", __name__, url_prefix="/api/v1/users")


@users_controller.route("/login", methods=["POST"])
@auto.doc()
def login():
    """
    LOGIN - POST /api/v1/users/login

    Validate credentials given and returns an authentication token if they are valid.
    Body {
      email: String,
      hws: String (Hashed Pass with Salt)
    }
    Returns {
        user: {
          "center_name": String,
          "designated_zone_name": String,
          "email":String,
          "phone": String,
          "gender": String,
          "is_active": Enum - ("Active", "Away"),
          "job_title": String,
          "language": String (ISO short for language E.g: 'en'),
          "name": String,
          "photo": String,
          "role": Enum - ("officer", "center-manager", "general-manager"),
          "working_hours": String
          }
        auth_token: String - JWT
    }
    """
    if request.get_json() is None:
        abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
    email = request.get_json().get("email")
    salt, password = UserFacade.get_user_salt_and_pass(email)
    client_hashed_pass = request.get_json().get("hws")
    hashed_pass = hashlib.sha256(
        f"{client_hashed_pass}{salt}".encode("utf-8")
    ).hexdigest()
    if hashed_pass == password:
        resp = UserFacade.get_user(email)
        resp.update({"is_active": "Active"})
        UserFacade.update_user(resp, email)
        token = encode_auth_token(email, resp.get("role"))
        active_tokens.append(token)
        return jsonify({"user": resp, "auth_token": token})
    else:
        abort(make_response(jsonify(error=USER_OR_PASSWORD_INCORRECT), 400))


@users_controller.route("/register", methods=["POST"])
@auto.doc()
@protected_endpoint(["center-manager", "general-manager"])
def register():
    """
    REGISTER - POST /api/v1/users/register

    Creates new users credentials. Only accessible for Center and General Managers.
    Header {
      Authorization: Auth Token - JWT
    }
    Body {
      center_name: String
      designated_zone_name: String
      email: String
      hashed_pass: String
      "phone": String,
      "gender": String,
      job_title: String
      name: String
      role: Enum - ("officer", "center-manager", "general-manager"),
      working_hours: String
    }

    Returns {
       "msg":"User registered successfully"
       }

    }
    """
    new_user = request.get_json()
    UserFacade.create_user(new_user)
    return jsonify({"msg": "User registered successfully"})


@users_controller.route("/logout", methods=["GET"])
@auto.doc()
@protected_endpoint()
def logout():
    """
    LOGOUT - GET /api/v1/users/logout

    Updates user status to Away
    Header {
      Authorization: Auth Token - JWT
    }

    Returns {
       "msg": "OK"
    }
    """
    auth_token = request.headers.get("Authorization")
    user_email = decode_auth_token(auth_token)[0]
    resp = UserFacade.get_user(user_email)
    resp.update({"is_active": "Away"})
    UserFacade.update_user(resp, user_email)
    token_index = active_tokens.index(auth_token)
    del active_tokens[token_index]
    return jsonify({"msg": "OK"})


@users_controller.route("/", methods=["PUT", "GET", "DELETE"])
@auto.doc()
@protected_endpoint(return_id=True)
def user_handler(user_id):
    """
    USER MANAGEMENT - GET /api/v1/users/

    Fetch the current logged in user.
    Header {
      Authorization: Auth Token - JWT
    }

    Returns {
          "center_name": String,
          "designated_zone_name": String,
          "email":String,
          "is_active": Enum - ("Active", "Away"),
          "job_title": String,
          "language": String (ISO short for language E.g: 'en'),
          "name": String,
          "phone": String,
          "gender": String,
          "photo": String,
          "role": Enum - ("officer", "center-manager", "general-manager"),
          "working_hours": String
          }

    USER MANAGEMENT - PUT /api/v1/users/

    Updates the user given by the email.
    Header {
      Authorization: Auth Token - JWT
    }

    Body {
          "center_name": String,
          "designated_zone_name": String,
          "email":String,
          "is_active": Enum - ("Active", "Away"),
          "job_title": String,
          "language": String (ISO short for language E.g: 'en'),
          "name": String,
          "phone": String,
          "gender": String,
          "photo": String,
          "role": Enum - ("officer", "center-manager", "general-manager"),
          "working_hours": String
          }

    Returns {
          "center_name": String,
          "designated_zone_name": String,
          "email":String,
          "is_active": Enum - ("Active", "Away"),
          "job_title": String,
          "phone": String,
          "gender": String,
          "language": String (ISO short for language E.g: 'en'),
          "name": String,
          "photo": String,
          "role": Enum - ("officer", "center-manager", "general-manager"),
          "working_hours": String
          }


    USER MANAGEMENT - DELETE /api/v1/users/

    Deletes user given by the email and center
    Header {
      Authorization: Auth Token - JWT
    }

    Params:
      - center: String ( Center Name )
      - email: String ( User ID )
    """
    if request.method == "PUT":
        new_user = request.get_json()
        resp = UserFacade.update_user(new_user, user_id)
        return jsonify(resp)

    if request.method == "GET":
        resp = UserFacade.get_user(user_id)
        if resp:
            resp.update({"is_active": "Active"})
            resp = UserFacade.update_user(resp, user_id)
        return jsonify(resp)
    if request.method == "DELETE":
        if request.args is None:
            abort(make_response(jsonify(error=EMPTY_REQUEST), 400))
        center_name = request.args.get("center")
        email = request.args.get("email")
        resp = UserFacade.delete_user(user_id, center_name, email)
        return jsonify(resp)


@users_controller.route("/select/working_hours/", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_all_working_hours():
    """
    SELECT WORKING HOURS - GET /api/v1/users/select/working_hours/

    Gets the list of selectable working hours
    Header {
      Authorization: Auth Token - JWT
    }

    Returns List<String>
    """
    if request.method == "GET":
        resp = UserFacade.get_all_working_hours()
        return jsonify(resp)


@users_controller.route("/select/status/", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_all_user_status():
    """
    SELECT USER STATUS - GET /api/v1/users/select/status/

    Gets the list of selectable user status
    Header {
      Authorization: Auth Token - JWT
    }

    Returns List<String>
    """
    if request.method == "GET":
        resp = UserFacade.get_all_user_status()
        return jsonify(resp)


@users_controller.route("/select/languages/", methods=["GET"])
@auto.doc()
@protected_endpoint()
def get_all_languages():
    """
    SELECT LANGUAGES - GET /api/v1/users/select/languages/

    Gets the list of selectable languages
    Header {
      Authorization: Auth Token - JWT
    }

    Returns List<String>
    """
    if request.method == "GET":
        resp = UserFacade.get_all_languages()
        return jsonify(resp)
