from flask import Blueprint, request, jsonify, abort, make_response
from .calibration_facade import CalibrationFacade
from .calibration_utils import camera_update_center_name
from app.auth_tools import protected_endpoint
from app import auto


calibration_controller = Blueprint(
    "calibration", __name__, url_prefix="/api/v1/calibration"
)


@calibration_controller.route("/camera_calibration", methods=["POST"])
@auto.doc()
@protected_endpoint(["center-manager", "general-manager"])
def add_camera_blueprint_relation():
    """
    UPDATE OR CREATE CAMERAS - POST /api/v1/calibration/camera_calibration

    Updates and create cameras given in form of list

    Header {
      Authorization: Auth Token - JWT
    }

    Body {
        cameraConfig: {
            name: String (Center's name)
            cameras: [
                {
                    cameraRTSP: String (RTSP URL)
                    camera_coords: List<List<Integer>(2)>
                    camera_id: String
                    camera_img: String (Base64)
                    camera_position: [Integer(2)]
                    center_name: String
                    encoding: String
                    floor_coords: List<List<Integer>(2)>
                    focal_length: Float
                    resolution: {
                        width: Integer,
                        height: Integer
                    }
                }
            ]
        }
    }

    Returns a list of messages. One for each camera in the list:
        [
            {msg: "Updated"}
        ]
    """
    if request.method == "POST":
        data = request.get_json().get("cameraConfig")
        if data is None:
            abort(400)
        cameras = data.get("cameras")
        center_name = data.get("name")
        if cameras is None or center_name is None:
            abort(400)
        cameras = map(camera_update_center_name(center_name), cameras)
        calibration_status = [
            CalibrationFacade.add_camera_blueprint_relation(camera)
            for camera in cameras
        ]
        return jsonify(calibration_status)


@calibration_controller.route("/camera_calibration", methods=["DELETE"])
@auto.doc()
@protected_endpoint(["center-manager", "general-manager"])
def delete_camera():
    """
    DELETE CAMERA - DELETE /api/v1/calibration/camera_calibration
    Deletes a camera from the database

    Header {
      Authorization: Auth Token - JWT
    }

    Params:
     - center_name
     - camera_id

    Returns:
     {msg: OK}
    """
    if request.method == "DELETE":
        if request.args is None:
            abort(400)
        center_name = request.args.get("center_name")
        camera_id = request.args.get("camera_id")
        resp = CalibrationFacade.delete_camera(center_name, camera_id)
        return jsonify(resp)
