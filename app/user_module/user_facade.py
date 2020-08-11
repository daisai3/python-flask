from flask import jsonify, abort, make_response
from cassandra.cqlengine.query import BatchQuery
from .user_models import UsersByLocation, User, UserStatus, WorkingHours, Language
from app.center_module.center_models import Center
import cassandra
from app.utils import (
    gen_salt,
    validate_email,
    authorized_roles,
    EMPTY_REQUEST,
    INVALID_FORMAT,
    NULL_PARAMS,
    CENTER_NOT_FOUND,
    USER_OR_PASSWORD_INCORRECT,
)
import base64
import hashlib


def _user_response_handler(current_user, img_encoding="data:image/png;base64"):
    photo = current_user.get("photo")
    if photo is not None:
        base64_encoded_data = base64.b64encode(photo)
        current_user.update(
            {"photo": f'{img_encoding},{base64_encoded_data.decode("utf-8")}'}
        )
    if current_user.get("hashed_pass") is not None:
        del current_user["hashed_pass"]
        del current_user["salt"]
    return current_user


def _update_user_by_center(requester, user, old_user, image):
    old_user_center = old_user.get("center_name")
    user_center = user.get("center_name")
    user_email = user.get("email")
    if (
        requester.get("role") == "center-manager"
        or requester.get("role") == "general-manager"
    ):
        try:
            new_center_exists = Center.objects(name=user_center).get()
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

        if old_user_center != user_center:
            UsersByLocation.objects(
                center_name=old_user_center, email=user_email
            ).delete()
            UsersByLocation.create(
                name=user.get("name"),
                job_title=user.get("job_title"),
                email=user_email,
                photo=image,
                center_name=user_center,
                designated_zone_name=user.get("designated_zone_name"),
                working_hours=user.get("working_hours"),
                is_active=user.get("is_active"),
                language=user.get("language"),
                role=old_user.get("role"),
            )
        else:
            UsersByLocation.objects(
                center_name=old_user_center, email=user_email
            ).update(
                photo=image,
                designated_zone_name=user.get("designated_zone_name"),
                working_hours=user.get("working_hours"),
                is_active=user.get("is_active"),
                job_title=user.get("job_title"),
                language=user.get("language"),
                role=user.get("role"),
            )
    if requester.get("role") == "officer":
        UsersByLocation.objects(
            center_name=requester.get("center_name"), email=requester.get("email")
        ).update(
            photo=image,
            designated_zone_name=user.get("designated_zone_name"),
            working_hours=user.get("working_hours"),
            is_active=user.get("is_active"),
            language=user.get("language"),
        )


class UserFacade:
    @staticmethod
    def create_user(user):
        if (
            user is None
            or user.get("center_name") is None
            or user.get("designated_zone_name") is None
            or user.get("email") is None
            or user.get("hashed_pass") is None
            or user.get("job_title") is None
            or user.get("name") is None
            or user.get("role") is None
            or user.get("working_hours") is None
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        if (
            not validate_email(user.get("email"))
            or user.get("role") not in authorized_roles
        ):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        salt = gen_salt()
        hashed_pass = hashlib.sha256(
            f"{user.get('hashed_pass')}{salt}".encode("utf-8")
        ).hexdigest()
        try:
            center_exists = Center.objects(name=user.get("center_name")).get()
            if center_exists:
                User.if_not_exists().create(
                    email=user.get("email"),
                    hashed_pass=hashed_pass,
                    salt=salt,
                    name=user.get("name"),
                    job_title=user.get("job_title"),
                    role=user.get("role"),
                    center_name=user.get("center_name"),
                    designated_zone_name=user.get("designated_zone_name"),
                    working_hours=user.get("working_hours"),
                    is_active="Away",
                    language="en",
                    phone=user.get("phone"),
                    gender=user.get("gender"),
                )

                UsersByLocation.if_not_exists().create(
                    email=user.get("email"),
                    center_name=user.get("center_name"),
                    working_hours=user.get("working_hours"),
                    is_active="Away",
                    name=user.get("name"),
                    job_title=user.get("job_title"),
                    designated_zone_name=user.get("designated_zone_name"),
                    role=user.get("role"),
                    language="en",
                )
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error="Email already in use"), 400))

    @staticmethod
    def get_user(email):
        if email is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            query = User.objects(email=email).get()
            user_response = _user_response_handler(dict(query))
            return user_response
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=USER_OR_PASSWORD_INCORRECT), 400))

    @staticmethod
    def get_user_salt_and_pass(email):
        if not email:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            query = User.objects(email=email).only(["salt", "hashed_pass"]).get()
            resp = dict(query)
            return resp.get("salt"), resp.get("hashed_pass")
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=USER_OR_PASSWORD_INCORRECT), 400))

    @staticmethod
    def update_user(user, requester_id):
        if (
            user is None
            or user.get("center_name") is None
            or user.get("center_name") == ""
            or user.get("email") is None
            or user.get("email") == ""
            or user.get("role") is None
            or user.get("role") == ""
            or user.get("designated_zone_name") is None
            or user.get("designated_zone_name") == ""
            or user.get("is_active") is None
            or user.get("is_active") == ""
            or user.get("job_title") is None
            or user.get("job_title") == ""
            or user.get("language") is None
            or user.get("language") == ""
            or user.get("name") is None
            or user.get("name") == ""
            or user.get("working_hours") is None
            or user.get("working_hours") == ""
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        image_base64 = user.get("photo")
        decoded_image_data = None
        if image_base64 is not None:
            img_encoding = image_base64.split(",")
            img_bytes = img_encoding[1].encode("utf-8")
            decoded_image_data = base64.decodebytes(img_bytes)
        try:
            user_requesting = dict(User.objects(email=requester_id).get())
            user_before_update = dict(User.objects(email=user.get("email")).get())
            new_center_exists = Center.objects(name=user.get("center_name")).get()
            if new_center_exists and (
                user_requesting.get("role") == "center-manager"
                or user_requesting.get("role") == "general-manager"
            ):
                User.objects(email=user.get("email")).if_exists().update(
                    photo=decoded_image_data,
                    designated_zone_name=user.get("designated_zone_name"),
                    working_hours=user.get("working_hours"),
                    is_active=user.get("is_active"),
                    language=user.get("language"),
                    job_title=user.get("job_title"),
                    center_name=user.get("center_name"),
                    role=user.get("role"),
                    phone=user.get("phone"),
                    gender=user.get("gender"),
                )
            elif user_requesting.get("role") == "officer" and user.get(
                "email"
            ) == user_requesting.get("email"):
                User.objects(email=user_requesting.get("email")).if_exists().update(
                    photo=decoded_image_data,
                    designated_zone_name=user.get("designated_zone_name"),
                    working_hours=user.get("working_hours"),
                    is_active=user.get("is_active"),
                    language=user.get("language"),
                    phone=user.get("phone"),
                    gender=user.get("gender"),
                )
            else:
                abort(
                    make_response(
                        jsonify(
                            error="Higher permissions needed to modify other users"
                        ),
                        403,
                    )
                )
            _update_user_by_center(
                user_requesting, user, user_before_update, decoded_image_data
            )
            updated_user = dict(User.objects(email=user.get("email")).get())
            user_response = _user_response_handler(updated_user)
            return user_response
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error="User or User's Center not found"), 400))
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error="User to update not found"), 400))

    @staticmethod
    def delete_user(user_id, center_name, email):
        if center_name is None or email is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            center_exists = Center.objects(name=center_name).get()
            if center_exists:
                User.objects(email=email).if_exists().delete()
                UsersByLocation.objects(
                    center_name=center_name, email=email
                ).if_exists().delete()
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error="User does not exists"), 400))

    @staticmethod
    def get_employees_from_center(center):
        try:
            center_exists = Center.objects(name=center).get()
            if center_exists:
                query = UsersByLocation.objects(center_name=center).all()
                employee_ids = [employee.email for employee in query]
                queryEmployees = User.objects(email__in=employee_ids).all()
                employee_list = [
                    _user_response_handler(dict(employee))
                    for employee in queryEmployees
                ]
                return employee_list
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_all_working_hours():
        query = WorkingHours.objects().all()
        working_hours_list = [item.type for item in query]
        return working_hours_list

    @staticmethod
    def get_all_user_status():
        query = UserStatus.objects().all()
        status_list = [item.status for item in query]
        return status_list

    @staticmethod
    def get_all_languages():
        query = Language.objects().all()
        languages_list = [
            {"key": language.iso_string, "value": language.name} for language in query
        ]
        return languages_list
