from flask import abort
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns, connection
from app.center_module.center_models import Center
from app.calibration_module.calibration_models import Calibration
from .calibration_utils import (
    camera_response_handler,
    is_valid_RTSP_url,
    is_valid_encoding,
    is_valid_resolution,
)
from app.utils import is_list_of_coords, is_base64
import cv2 as cv
import cassandra
import random
import json
import numpy as np


class CalibrationFacade:
    @staticmethod
    def add_camera_blueprint_relation(camera_config):
        if (
            camera_config.get("camera_coords") is None
            or not is_list_of_coords(camera_config.get("camera_coords"))
            or camera_config.get("floor_coords") is None
            or not is_list_of_coords(camera_config.get("floor_coords"))
            or camera_config.get("camera_position") is None
            or not is_list_of_coords(camera_config.get("camera_position"))
            or len(camera_config.get("camera_position")) != 1
            or camera_config.get("cameraRTSP") is None
            or not is_valid_RTSP_url(camera_config.get("cameraRTSP"))
            or camera_config.get("encoding") is None
            or not is_valid_encoding(camera_config.get("encoding"))
            or camera_config.get("focal_length") is None
            or float(camera_config.get("focal_length")) < 0
            or camera_config.get("resolution") is None
            or not is_valid_resolution(camera_config.get("resolution"))
            or camera_config.get("camera_img") is None
            or not is_base64(camera_config.get("camera_img"))
        ):
            abort(400)
        try:
            center_exist = Center.objects(name=camera_config.get("name")).get()
            if center_exist:
                camera_coords = np.array(camera_config.get("camera_coords"))
                floor_coords = np.array(camera_config.get("floor_coords"))

                mtx = cv.findHomography(camera_coords, floor_coords)

                calibration_info = {
                    "floor_coords": floor_coords.tolist(),
                    "camera_coords": camera_coords.tolist(),
                    "calibration_matrix": np.asarray(mtx[0]).tolist(),
                    "camera_position": camera_config.get("camera_position"),
                    "cameraRTSP": camera_config.get("cameraRTSP"),
                    "encoding": camera_config.get("encoding"),
                    "focal_length": camera_config.get("focal_length"),
                    "resolution": camera_config.get("resolution"),
                    "camera_img": camera_config.get("camera_img"),
                }
                query = (
                    Calibration.objects(
                        center_name=camera_config.get("name"),
                        camera_id=camera_config.get("camera_id"),
                    )
                    .if_exists()
                    .update(
                        calibration_info=json.dumps(calibration_info).encode("utf-8")
                    )
                )
            return {"msg": "Updated"}

        except cassandra.cqlengine.query.LWTException:
            query = Calibration.create(
                center_name=camera_config.get("name"),
                camera_id=camera_config.get("camera_id"),
                calibration_info=json.dumps(calibration_info).encode("utf-8"),
            )
            return {"msg": "Created"}
        except cassandra.cqlengine.query.DoesNotExist:
            abort(400)

    @staticmethod
    def get_center_cameras(center_name):
        result = Calibration.objects(center_name=center_name).all()

        return [camera_response_handler(camera) for camera in result]

    @staticmethod
    def delete_camera(center_name, camera_id):
        if center_name is None or camera_id is None:
            abort(400)
        try:
            Calibration.objects(
                center_name=center_name, camera_id=camera_id
            ).if_exists().delete()
            return {"msg": "OK"}
        except (
            cassandra.cqlengine.query.LWTException,
            cassandra.cqlengine.query.DoesNotExist,
        ):
            abort(400)
