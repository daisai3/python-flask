from flask import abort, make_response, jsonify
from app.center_module.center_models import Center
from .timeline_models import Timeline, CustomerTracker, DwellTime
from app.center_module.center_models import Areas
from .timeline_utils import (
    history_type_values,
    sortByArea,
    stage_timeline_mapper,
    happiness_timeline_mapper,
    footage_timeline_mapper,
    history_happiness_mapper,
)
from app.utils import (
    NULL_PARAMS,
    INVALID_FORMAT,
    INVALID_TIME_RANGES,
    CENTER_NOT_FOUND,
    CUSTOMER_NOT_FOUND,
    create_area_mapper,
)
import base64
import cassandra
import pandas as pd
import numpy as np
import cv2
import json


class TimelineFacade:
    @staticmethod
    def get_stages_timeline(center_name, customer_id, start_time):
        if customer_id is None or start_time is None or center_name is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                query = Timeline.objects(
                    center_name=center_name, epoch_second__gte=int(start_time),
                ).all()
                stages_timeline = [
                    stage_timeline_mapper(frame)
                    for frame in query
                    if frame.global_identity == customer_id
                ]
                if len(stages_timeline) == 0:
                    abort(make_response(jsonify(error=CUSTOMER_NOT_FOUND), 400))
                return stages_timeline
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_happiness_timeline(center_name, customer_id, start_time):
        if customer_id is None or start_time is None or center_name is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                query = Timeline.objects(
                    center_name=center_name, epoch_second__gte=int(start_time),
                ).all()
                happiness_timeline = [
                    happiness_timeline_mapper(frame)
                    for frame in query
                    if dict(frame).get("global_identity") == customer_id
                ]
                if len(happiness_timeline) == 0:
                    abort(make_response(jsonify(error=CUSTOMER_NOT_FOUND), 400))
                return happiness_timeline
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_footage_timeline(center_name, customer_id, start_time):
        if customer_id is None or start_time is None or center_name is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                query = Timeline.objects(
                    center_name=center_name, epoch_second__gte=int(start_time),
                ).all()
                footage_timeline = [
                    footage_timeline_mapper(frame)
                    for frame in query
                    if dict(frame).get("global_identity") == customer_id
                ]
                if len(footage_timeline) == 0:
                    abort(make_response(jsonify(error=CUSTOMER_NOT_FOUND), 400))

                footage_timeline = [
                    face_crop for face_crop in footage_timeline if face_crop is not None
                ]
                return footage_timeline
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_history(center, history_type, start_time, end_time, time_interval, role):
        if (
            center is None
            or history_type is None
            or start_time is None
            or end_time is None
            or time_interval is None
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        if (
            time_interval <= 0
            or history_type not in history_type_values
            or start_time >= end_time
        ):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        if center == "ALL" and role == "general-manager":
            centers = Center.objects().all()
            center_list = [center.name for center in centers]
            customers = Timeline.objects(
                center_name__in=center_list,
                epoch_second__gte=int(start_time),
                epoch_second__lte=int(end_time),
            ).all()
        else:
            try:
                center_exist = Center.objects(name=center).get()
            except cassandra.cqlengine.query.DoesNotExist:
                abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))
            if center_exist:
                customers = Timeline.objects(
                    center_name=center,
                    epoch_second__gte=int(start_time),
                    epoch_second__lte=int(end_time),
                ).all()

        list_timelines = [
            (
                timeline.epoch_second,
                timeline.gender,
                timeline.ethnicity,
                timeline.age,
                timeline.happiness,
            )
            for timeline in customers
        ]

        list_timelines = [timeline for timeline in list_timelines if all(timeline)]

        df_db = pd.DataFrame(
            list_timelines,
            columns=["epoch_second", "gender", "ethnicity", "age", "happiness"],
        )
        if len(df_db) <= 0:
            return []
        df_db["epoch_second_interval"] = df_db.apply(
            lambda row: int(row.epoch_second / time_interval), axis=1
        )
        list_epoch_interval = list(df_db["epoch_second_interval"].unique())

        if history_type == "happiness":
            df_grouped_gender = (
                df_db[["epoch_second_interval", "gender", "happiness"]]
                .groupby(["epoch_second_interval", "gender"], as_index=False)
                .mean()
            )
            df_grouped_ethnicity = (
                df_db[["epoch_second_interval", "ethnicity", "happiness"]]
                .groupby(["epoch_second_interval", "ethnicity"], as_index=False)
                .mean()
            )
            df_grouped_age = (
                df_db[["epoch_second_interval", "age", "happiness"]]
                .groupby(["epoch_second_interval", "age"], as_index=False)
                .mean()
            )

            return [
                history_happiness_mapper(
                    epoch_interval,
                    time_interval,
                    df_grouped_gender.loc[
                        df_grouped_gender["epoch_second_interval"] == epoch_interval
                    ],
                    df_grouped_ethnicity.loc[
                        df_grouped_ethnicity["epoch_second_interval"] == epoch_interval
                    ],
                    df_grouped_age.loc[
                        df_grouped_age["epoch_second_interval"] == epoch_interval
                    ],
                )
                for epoch_interval in list_epoch_interval
            ]
        elif history_type == "attendance":
            df_grouped_gender = (
                df_db[["epoch_second_interval", "gender", "happiness"]]
                .groupby(["epoch_second_interval", "gender"], as_index=False)
                .count()
            )
            df_grouped_ethnicity = (
                df_db[["epoch_second_interval", "ethnicity", "happiness"]]
                .groupby(["epoch_second_interval", "ethnicity"], as_index=False)
                .count()
            )
            df_grouped_age = (
                df_db[["epoch_second_interval", "age", "happiness"]]
                .groupby(["epoch_second_interval", "age"], as_index=False)
                .count()
            )

            return [
                history_happiness_mapper(
                    epoch_interval,
                    time_interval,
                    df_grouped_gender.loc[
                        df_grouped_gender["epoch_second_interval"] == epoch_interval
                    ],
                    df_grouped_ethnicity.loc[
                        df_grouped_ethnicity["epoch_second_interval"] == epoch_interval
                    ],
                    df_grouped_age.loc[
                        df_grouped_age["epoch_second_interval"] == epoch_interval
                    ],
                )
                for epoch_interval in list_epoch_interval
            ]

    @staticmethod
    def get_journey_summary(center, from_time, to_time):
        if (
            center is None
            or from_time is None
            or to_time is None
            or from_time > to_time
        ):
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400
                )
            )

        try:
            center_exists = Center.objects(name=center).get()
        except cassandra.cqlengine.query.DoesNotExist:
            return abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

        if center_exists:
            timeframes_list = Timeline.objects(
                center_name=center,
                epoch_second__gte=from_time,
                epoch_second__lte=to_time,
            ).all()

            area_hx_per_id_list = [
                (frame.global_identity, frame.area_type, frame.area, frame.happiness)
                for frame in timeframes_list
            ]
            df_db = pd.DataFrame(
                area_hx_per_id_list, columns=["id", "area_type", "area_name", "hx"]
            )

            df_db.drop(
                df_db[df_db.area_type.str.contains("Free") | df_db.hx.isnull()].index,
                inplace=True,
            )

            if len(df_db) <= 0:
                return {"areas_journey": [], "area_usage": []}

            df_db = (
                df_db[["id", "area_type", "area_name", "hx"]]
                .groupby(["id", "area_type", "area_name"], as_index=False)
                .mean()
            )

            df_db_usage = (
                df_db[["id", "area_name"]]
                .groupby(["area_name"], as_index=False)
                .count()
            )

            area_usage = [
                {
                    "area": item.area_name,
                    "value": (item.id / len(df_db)) if len(df_db) > 0 else 0,
                }
                for item in df_db_usage.itertuples()
            ]

            df_db_hx_per_type = (
                df_db[["area_type", "hx"]].groupby(["area_type"], as_index=False).mean()
            )
            areas_journey = [
                {"area_type": item.area_type, "value": item.hx}
                for item in df_db_hx_per_type.itertuples()
            ]
            areas_journey.sort(key=sortByArea)

            return {"areas_journey": areas_journey, "area_usage": area_usage}

    @staticmethod
    def get_most_traveled_journey(center, from_time, to_time):
        if center is None or from_time > to_time:
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400
                )
            )
        try:
            # getting unique entries of timeline sorted by timestamp
            center_exists = Center.objects(name=center).get()
            if center_exists:
                query = (
                    Timeline.objects(
                        center_name=center,
                        epoch_second__gte=from_time,
                        epoch_second__lte=to_time,
                    )
                    .order_by("epoch_second")
                    .all()
                )
                items = [
                    (item["global_identity"], item["area"], item["area_type"])
                    for item in query
                    if item["area_type"] != "Free"
                ]
                items = pd.Series(items).drop_duplicates().tolist()

                # Group by Global_id => transition list by client
                journeys = {}
                for item in items:
                    if journeys.get(item[0]) is None:
                        journeys[item[0]] = []
                    journeys[item[0]].append(item[1])

                # split into groups of n
                n = 3
                for customer, values in journeys.items():
                    full_journey = journeys[customer]
                    splitted_journey = []
                    for i, stage in enumerate(full_journey):
                        # if len(full_journey) < n:
                        #     splitted_journey.append(tuple(full_journey))
                        if i + n <= len(full_journey):
                            split = full_journey[i : i + n]
                            splitted_journey.append(tuple(split))
                    journeys[customer] = splitted_journey

                # get percentage of usage
                num_of_clients = len(journeys)
                journey_counts = {}
                for item, values in journeys.items():
                    values = pd.Series(values).drop_duplicates().tolist()
                    for journey in values:
                        journey_id = "-".join(journey)
                        if journey_counts.get(journey_id) is None:
                            journey_counts[journey_id] = 1
                        else:
                            journey_counts[journey_id] += 1

                areas = Areas.objects().all()
                area_mapper = create_area_mapper(areas)

                journey_usage = []
                for item, values in journey_counts.items():
                    stages_names = item.split("-")
                    stages_names = list(map(area_mapper, stages_names))
                    journey_entry = {
                        "journey": stages_names,
                        "percent": values / num_of_clients,
                    }
                    journey_usage.append(journey_entry)
                return journey_usage
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_heatmap(center, from_time, to_time, global_identity=None):
        if (
            center is None
            or from_time is None
            or to_time is None
            or from_time > to_time
        ):
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400
                )
            )
        try:
            center_exists = Center.objects(name=center).get()
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))
        if center_exists:
            customers_history = Timeline.objects(
                center_name=center,
                epoch_second__gte=from_time,
                epoch_second__lte=to_time,
            ).all()

            if global_identity is not None:
                movement_history = [
                    (movement.position_x, movement.position_y, movement.epoch_second)
                    for movement in customers_history
                    if movement.global_identity == global_identity
                ]
            else:
                movement_history = [
                    (movement.position_x, movement.position_y, movement.epoch_second)
                    for movement in customers_history
                ]

            df_db = pd.DataFrame(movement_history, columns=["x", "y", "epoch_second"])
            if len(df_db) <= 0:
                return {"values": [], "max": 0}

            # Aggregation by squares of size N pixels, and reposition coord to center of square.
            square_size = 50
            df_db["x"] = df_db.apply(
                lambda row: int(row.x / square_size) * square_size + square_size / 2,
                axis=1,
            )
            df_db["y"] = df_db.apply(
                lambda row: int(row.y / square_size) * square_size + square_size / 2,
                axis=1,
            )
            df_grouped_coords = (
                df_db[["x", "y", "epoch_second"]]
                .groupby(["x", "y"], as_index=False)
                .count()
            )

            max_value = df_grouped_coords["epoch_second"].max()
            values_row = [
                {"x": int(row.x), "y": int(row.y), "value": row.epoch_second}
                for row in df_grouped_coords.itertuples()
            ]
            return {"values": values_row, "max": int(max_value)}

    @staticmethod
    def get_center_area_dwell_sum(center_name, from_time, to_time):
        if (
            center_name is None
            or from_time is None
            or to_time is None
            or from_time > to_time
        ):
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400
                )
            )

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                areas = Areas.objects(center_name=center_name).all()
                enconding = "utf-8"
                list_areas = [
                    {
                        "center_name": area.center_name,
                        "area_name": area.area_name,
                        "area_type": area.area_type,
                        "polygon": json.loads(area.polygon.decode(enconding)),
                        "dwell": 0,
                    }
                    for area in areas
                    if all(area)
                ]

                list_areas_name = [area["area_name"] for area in list_areas]
                customers = CustomerTracker.objects(center_name=center_name).all()
                list_timelines = [
                    (timeline.global_identity)
                    for timeline in customers
                    if all(timeline)
                ]

                df_db = pd.DataFrame(
                    list_timelines, columns=["global_identity"],
                ).dropna()
                if len(df_db) <= 0:
                    return {"areas": list_areas}

                global_identities = list(df_db["global_identity"].unique())
                customers = DwellTime.objects(
                    center_name=center_name,
                    global_identity__in=global_identities,
                    area__in=list_areas_name,
                    epoch_second__gte=int(from_time),
                    epoch_second__lte=int(to_time),
                ).all()

                list_timelines = [
                    (timeline.area, timeline.dwell_time)
                    for timeline in customers
                    if all(timeline)
                ]

                df_db = pd.DataFrame(
                    list_timelines, columns=["area", "dwell_time"],
                ).dropna()

                if len(df_db) <= 0:
                    return {"areas": list_areas}

                df_dwell = df_db.groupby("area", as_index=False).sum()
                if len(df_dwell) <= 0:
                    return {"areas": list_areas}
                for area in list_areas:
                    df_area = df_dwell[df_dwell["area"] == area["area_name"]]
                    if len(df_area) > 0:
                        area["dwell"] = round(df_area["dwell_time"].iloc[0], 2)

                return {"areas": list_areas}
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_dwell_heatmap(center, from_time, to_time):
        areas_dwell_info = TimelineFacade.get_center_area_dwell_sum(
            center, from_time, to_time
        )
        points = TimelineFacade.get_heatmap(center, from_time, to_time)
        list_points = []
        max = 0
        for point in points["values"]:
            if "x" in point and "y" in point and "value" in point:
                for area in areas_dwell_info["areas"]:
                    ctr = np.array(area["polygon"]).reshape((-1, 1, 2)).astype(np.int32)
                    if (
                        cv2.pointPolygonTest(
                            ctr, tuple((point["x"], point["y"])), False
                        )
                        >= 0
                    ):
                        if point.get("value", 0) > 0:
                            point["dwell"] = int(area["dwell"] / point["value"])
                        else:
                            point["dwell"] = 0
                        if point.get("value") is not None:
                            del point["value"]
                        list_points.append(point)
                        if point["dwell"] > max:
                            max = point["dwell"]

        return {"max": max, "values": list_points}

    @staticmethod
    def get_historic_attendance(center, from_time, to_time):
        if center is None or from_time > to_time:
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400
                )
            )
        try:
            center_exists = Center.objects(name=center).get()
            if center_exists:
                query = Timeline.objects(
                    center_name=center,
                    epoch_second__gte=from_time,
                    epoch_second__lte=to_time,
                ).all()
                checked_id_list = []
                response = {
                    "total_customers": 0,
                    "Female": 0,
                    "Male": 0,
                    "Local": 0,
                    "Non": 0,
                    "mask_on": 0,
                }
                for customer in query:
                    if customer.global_identity not in checked_id_list:
                        checked_id_list.append(customer.global_identity)
                        if customer.gender is not None:
                            response[customer.gender] += 1
                        if customer.ethnicity is not None:
                            response[customer.ethnicity] += 1
                        if customer.mask == "Mask":
                            response["mask_on"] += 1
                response["total_customers"] = len(checked_id_list)
                return response
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

