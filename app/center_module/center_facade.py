from flask import abort, make_response, jsonify
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.query import BatchQuery
from cassandra.cqlengine import columns, connection
from app.timeline_module.timeline_models import CustomerTracker, DwellTime, Timeline
from app.user_module.user_facade import UserFacade
from .center_models import Center, Areas
import datetime
from app.calibration_module.calibration_facade import CalibrationFacade
from app.utils import (
    validate_email,
    bytes2b64string,
    bytes2json,
    area_response_handler,
    is_base64,
    is_list_of_coords,
    is_valid_area,
    add_dwell_time_to_customer,
    NULL_PARAMS,
    INVALID_TIME_RANGES,
    CENTER_NOT_FOUND,
    INVALID_FORMAT,
    AREA_NOT_FOUND,
    INVALID_TIME_RANGES,
    INVALID_PAGE_NUMBER,
)
import cassandra
import numpy as np
import json
import functools
import base64
import pandas as pd

area_highlight_type = "type"
area_highlight_name = "name"
entry_area_type = "Entry"
exit_area_type = "Exit"
default_entrance_area = "Main Entrance"


class CenterFacade:
    @staticmethod
    def get_center_info(name, from_time, to_time):
        if name is None or from_time is None or to_time is None or from_time > to_time:
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400,
                )
            )

        try:
            response = {}
            center_info = dict(Center.objects(name=name).get())
            if center_info.get("floor_plan"):
                floor_plan = {
                    "floor_plan": bytes2b64string(center_info.get("floor_plan")),
                }
                center_info.update(floor_plan)
            if center_info.get("distance_points"):
                distance_points = {
                    "distance_points": bytes2json(center_info.get("distance_points")),
                }
                center_info.update(distance_points)

            response.update(center_info)

            center_cameras = CalibrationFacade.get_center_cameras(name)

            response.update({"cameras": center_cameras})

            center_client_ids_list = CenterFacade.get_client_list(
                name, from_time, to_time
            )
            avg_waiting_time = 0
            if len(center_client_ids_list) > 0:
                avg_waiting_time = sum(
                    [
                        client["dwell_time"]
                        for client in center_client_ids_list
                        if client["dwell_time"] is not None
                    ]
                ) // len(center_client_ids_list)

            response.update({"avg_waiting_time": avg_waiting_time})

            response.update({"customer_list": center_client_ids_list})

            center_employee_list = UserFacade.get_employees_from_center(name)
            response.update({"employee_list": center_employee_list})

            return response
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_center_aggregations(name):
        try:
            # Todo: gathering information for reports
            pass
        except cassandra.cqlengine.query.DoesNotExist:
            pass

    @staticmethod
    def get_client_list(name, from_time, to_time):
        if name is None or from_time is None or to_time is None or from_time > to_time:
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400,
                )
            )

        try:
            query = CustomerTracker.objects(center_name=name).all()
            in_store_clients_ids = [
                dict(client) for client in query if client.area is not None
            ]
            waiting_areas = Areas.objects(center_name=name, area_type="Waiting").all()
            waiting_areas = [area.area_name for area in waiting_areas]
            for client in in_store_clients_ids:
                query = DwellTime.objects(
                    center_name=name,
                    global_identity=client["global_identity"],
                    area__in=waiting_areas,
                    epoch_second__gt=int(from_time),
                    epoch_second__lt=int(to_time),
                ).all()

                waiting_time = sum(
                    [
                        client.dwell_time
                        for client in query
                        if client.area in waiting_areas
                        and client.dwell_time is not None
                    ]
                )
                client["dwell_time"] = waiting_time

            return in_store_clients_ids
        except cassandra.cqlengine.query.DoesNotExist:
            pass

    @staticmethod
    def update_center_info(role, new_data):
        if (
            new_data.get("name") is None
            or new_data.get("floor_plan") is None
            or new_data.get("scale_meters") is None
            or new_data.get("distance_points") is None
            or new_data.get("floor_plan_scale") is None
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400,))
        if not is_base64(new_data.get("floor_plan")) or not is_list_of_coords(
            new_data.get("distance_points")
        ):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400,))
        floor_plan_str = new_data.get("floor_plan")
        base64_part = floor_plan_str.split(",")[1]
        floor_plan_encoded = base64_part.encode("utf-8")
        floor_plan_in_bytes = base64.decodebytes(floor_plan_encoded)

        distance_bytes = json.dumps(new_data.get("distance_points")).encode("utf-8")
        try:
            if role == "general-manager":
                if (
                    new_data.get("location") is None
                    or new_data.get("manager_name") is None
                    or new_data.get("manager_email") is None
                ):
                    abort(make_response(jsonify(error=NULL_PARAMS), 400))
                if not validate_email(new_data.get("manager_email")):
                    abort(make_response(jsonify(error=INVALID_FORMAT), 400))
                Center.objects(name=new_data.get("name")).if_exists().update(
                    location=new_data.get("location"),
                    manager_name=new_data.get("manager_name"),
                    manager_email=new_data.get("manager_email"),
                    floor_plan=floor_plan_in_bytes,
                    scale_meters=float(new_data.get("scale_meters")),
                    distance_points=distance_bytes,
                    floor_plan_px_per_meter=float(new_data.get("floor_plan_scale")),
                )
            if role == "center-manager":
                Center.objects(name=new_data.get("name")).if_exists().update(
                    floor_plan=floor_plan_in_bytes,
                    scale_meters=new_data.get("scale_meters"),
                    distance_points=distance_bytes,
                    floor_plan_px_per_meter=new_data.get("floor_plan_scale"),
                )
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

        updated_center = Center.objects(name=new_data.get("name")).get()
        updated_center = dict(updated_center)

        updated_center.update(
            {
                "floor_plan": bytes2b64string(updated_center.get("floor_plan")),
                "distance_points": bytes2json(updated_center.get("distance_points")),
            }
        )
        return updated_center

    @staticmethod
    def get_all_centers_name():
        query = Center.objects().only(["name"]).all()
        names_list = [center.name for center in query]
        try:
            return names_list
        except cassandra.cqlengine.query.DoesNotExist:
            pass

    @staticmethod
    def get_all_zones(center_name):
        if center_name is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                query = Areas.objects(center_name=center_name).all()
                area_list = [area_response_handler(area) for area in query]
                return area_list
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_all_zones_name(center_name):
        if center_name is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            center_exists = Center.objects(name=center_name).get()
            if center_exists:
                query = Areas.objects(center_name=center_name).all()
                return list(set([area.area_name for area in query]))
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def update_zone(old_zone, new_zone):
        if old_zone is None or new_zone is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        if not is_valid_area(old_zone) or not is_valid_area(new_zone):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))

        if old_zone.get("center_name") != new_zone.get("center_name"):
            abort(
                make_response(
                    jsonify(error="Changing an area's center is not possible."), 403
                )
            )

        byte_coords = json.dumps(new_zone.get("polygon")).encode("utf-8")
        query = None
        dif_area_type = old_zone.get("area_type") != new_zone.get("area_type")
        dif_area = old_zone.get("area_name") != new_zone.get("area_name")
        try:
            new_area_exists = Areas.objects(
                center_name=new_zone.get("center_name"),
                area_type=new_zone.get("area_type"),
                area_name=new_zone.get("area_name"),
            ).get()
            if new_area_exists:
                abort(
                    make_response(
                        jsonify(
                            error="The area you are trying to update to, already exists."
                        ),
                        403,
                    )
                )
        except cassandra.cqlengine.query.DoesNotExist:
            pass

        try:
            if dif_area or dif_area_type:
                batch = BatchQuery()
                Areas.objects(
                    center_name=old_zone.get("center_name"),
                    area_type=old_zone.get("area_type"),
                    area_name=old_zone.get("area_name"),
                ).if_exists().batch(batch).delete()
                query = (
                    Areas.batch(batch)
                    .if_not_exists()
                    .create(
                        center_name=new_zone.get("center_name"),
                        area_type=new_zone.get("area_type"),
                        area_name=new_zone.get("area_name"),
                        polygon=byte_coords,
                    )
                )
                batch.execute()
                area = dict(query)
                area.update({"polygon": bytes2json(area.get("polygon"))})
                return area
            else:
                Areas.objects(
                    center_name=old_zone.get("center_name"),
                    area_type=old_zone.get("area_type"),
                    area_name=old_zone.get("area_name"),
                ).if_exists().update(polygon=byte_coords)
                updated_area = old_zone
                updated_area.update({"polygon": new_zone.get("coords")})
                return updated_area
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error=AREA_NOT_FOUND), 400))

    @staticmethod
    def delete_zone(center_name, area, area_type):
        if center_name is None or area is None or area_type is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            Areas.objects(
                center_name=center_name, area_name=area, area_type=area_type
            ).if_exists().delete()
            return {"msg": "OK"}
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error=AREA_NOT_FOUND), 400))

    @staticmethod
    def create_zone(new_zone):
        if (
            new_zone is None
            or new_zone.get("polygon") is None
            or new_zone.get("center_name") is None
            or new_zone.get("area_name") is None
            or new_zone.get("area_name") == ""
            or new_zone.get("area_type") is None
            or new_zone.get("area_type") == ""
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        if not is_list_of_coords(new_zone.get("polygon")):
            abort(make_response(jsonify(error=INVALID_FORMAT), 400))
        byte_coords = json.dumps(new_zone.get("polygon")).encode("utf-8")
        try:
            center_exists = Center.objects(name=new_zone.get("center_name")).get()
            if center_exists:
                query = (
                    Areas.objects(
                        center_name=new_zone.get("center_name"),
                        area_name=new_zone.get("area_name"),
                        area_type=new_zone.get("area_type"),
                    )
                    .if_not_exists()
                    .create(
                        center_name=new_zone.get("center_name"),
                        area_name=new_zone.get("area_name"),
                        area_type=new_zone.get("area_type"),
                        polygon=byte_coords,
                    )
                )

                area = dict(query)
                area.update({"polygon": bytes2json(area.get("polygon"))})
                return area
        except cassandra.cqlengine.query.LWTException:
            abort(make_response(jsonify(error="This area already exists"), 400))

        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_center_waiting_stats(center, from_time, to_time, is_live):
        if (
            center is None
            or is_live is None
            or from_time is None
            or to_time is None
            or from_time > to_time
        ):
            abort(
                make_response(
                    jsonify(error="{NULL_PARAMS} and {INVALID_TIME_RANGES}"), 400
                )
            )

        customer_id_list = Timeline.objects(
            center_name=center, epoch_second__gte=from_time, epoch_second__lte=to_time
        ).all()
        customer_id_list = [customer.global_identity for customer in customer_id_list]
        customer_id_list = list(set(customer_id_list))
        waiting_areas = Areas.objects(center_name=center, area_type="Waiting").all()
        waiting_areas = [area.area_name for area in waiting_areas]

        if not is_live:
            customers_list = DwellTime.objects(
                center_name=center,
                global_identity__in=customer_id_list,
                area__in=waiting_areas,
            )
        else:
            customers_list = CustomerTracker.objects(
                center_name=center, global_identity__in=customer_id_list,
            )
            customers_list = [
                customer
                for customer in customers_list
                if customer.area in waiting_areas
            ]
            customers_list = list(map(add_dwell_time_to_customer, customers_list))

        total_waiting_time = functools.reduce(
            lambda acc, curr: acc + curr["dwell_time"], customers_list, 0,
        )

        area_attendance_dict = {}
        area_usage_dict = {}
        for customer in customers_list:
            if customer["area"] in waiting_areas:
                if area_attendance_dict.get(customer["area"]) is None:
                    area_attendance_dict[customer["area"]] = 1
                    area_usage_dict[customer["area"]] = customer["dwell_time"]
                else:
                    area_attendance_dict[customer["area"]] += 1
                    area_usage_dict[customer["area"]] += customer["dwell_time"]

        waiting_areas_attendance = [
            {"area": area[0], "amount": area[1]}
            for area in area_attendance_dict.items()
        ]
        waiting_factors = [
            {
                "area": area[0],
                "amount": (area[1] // 60 // area_attendance_dict[area[0]])
                if area_attendance_dict[area[0]] > 0
                else 0,
            }
            for area in area_usage_dict.items()
        ]
        total_ppl_waiting = len(
            list(set([customer["global_identity"] for customer in customers_list]))
        )

        return {
            "total_waiting_time": (total_waiting_time // 60 // total_ppl_waiting)
            if total_ppl_waiting > 0
            else 0,
            "waiting_areas_attendance": waiting_areas_attendance,
            "total_ppl_waiting": total_ppl_waiting,
            "waiting_factors": waiting_factors,
        }

    @staticmethod
    def get_areas_hx(center, from_time, to_time):
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
        query = Timeline.objects(
            center_name=center, epoch_second__gte=from_time, epoch_second__lte=to_time
        ).all()
        items = [
            dict(item)
            for item in query
            if item.happiness is not None and item["area_type"] != "Free"
        ]
        areas = CenterFacade.get_all_zones(center)

        area_values = {}
        for entry in items:
            if area_values.get(entry["area"]) is None:
                area_values[entry["area"]] = []
            area_values[entry["area"]].append(entry["happiness"])

        happiness_per_area = []

        for i, area in enumerate(areas):
            values = area_values.get(area.get("area_name"))
            if values is None:
                area.update({"happiness_avg": 0})
                happiness_per_area.append(area)
            else:
                values_len = len(values) if len(values) > 0 else 1
                avg = functools.reduce(lambda a, b: a + b, values, 0) / values_len
                area.update({"happiness_avg": avg})
                happiness_per_area.append(area)
        return happiness_per_area

    @staticmethod
    def takeCustomerEpochSecond(customer):
        return customer["epoch_second"]

    @staticmethod
    def takeCustomerJourneyEpochSecond(customer):
        return customer["epoch_second_entrance"]

    @staticmethod
    def get_customer_list(center_name, from_time, to_time, is_live, page, page_size):
        if (
            center_name is None
            or from_time is None
            or to_time is None
            or is_live is None
            or from_time > to_time
            or page_size < 1
            or page < 0
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:

                if is_live:
                    customers = CustomerTracker.objects(center_name=center_name).all()

                    list_timelines = [
                        (
                            customerTracker.center_name,
                            customerTracker.global_identity,
                            customerTracker.gender,
                            customerTracker.epoch_second,
                            customerTracker.happiness_index,
                            customerTracker.age_range,
                            customerTracker.ethnicity,
                            customerTracker.live_dwell_time,
                            customerTracker.area,
                            customerTracker.area_type,
                        )
                        for customerTracker in customers
                        if all(customerTracker)
                    ]
                    df_db = pd.DataFrame(
                        list_timelines,
                        columns=[
                            "center_name",
                            "global_identity",
                            "gender",
                            "epoch_second",
                            "happiness",
                            "age",
                            "ethnicity",
                            "live_dwell_time",
                            "area",
                            "area_type",
                        ],
                    )
                    if len(df_db) <= 0:
                        return {"total_customers": 0, "total_pages": 0, "customers": []}

                    global_identities = []
                    for index, row in df_db.iterrows():
                        global_identities.append(
                            {
                                "global_identity": row["global_identity"],
                                "epoch_second": row["epoch_second"],
                            }
                        )

                    global_identities.sort(
                        key=CenterFacade.takeCustomerEpochSecond, reverse=True
                    )

                else:
                    customers = Timeline.objects(
                        center_name=center_name,
                        epoch_second__gte=int(from_time),
                        epoch_second__lte=int(to_time),
                    ).all()
                    list_timelines = [
                        (
                            timeline.center_name,
                            timeline.epoch_second,
                            timeline.global_identity,
                            timeline.gender,
                            timeline.happiness,
                            timeline.age,
                            timeline.ethnicity,
                            timeline.area,
                            timeline.area_type,
                        )
                        for timeline in customers
                        if all(timeline)
                    ]

                    df_db = pd.DataFrame(
                        list_timelines,
                        columns=[
                            "center_name",
                            "epoch_second",
                            "global_identity",
                            "gender",
                            "happiness",
                            "age",
                            "ethnicity",
                            "area",
                            "area_type",
                        ],
                    )

                    if len(df_db) <= 0:
                        return {"total_customers": 0, "total_pages": 0, "customers": []}

                    global_identities = []
                    df_global_indentity = (
                        df_db[["global_identity", "epoch_second"]]
                        .groupby("global_identity", as_index=False)
                        .max()
                    )

                    for index, row in df_global_indentity.iterrows():
                        global_identities.append(
                            {
                                "global_identity": row["global_identity"],
                                "epoch_second": row["epoch_second"],
                            }
                        )

                    global_identities.sort(
                        key=CenterFacade.takeCustomerEpochSecond, reverse=True
                    )

                total_customers = len(global_identities)
                total_pages = int(total_customers / page_size)
                if total_customers % page_size != 0:
                    total_pages += 1
                if (page + 1) > total_pages:
                    abort(make_response(jsonify(error=INVALID_PAGE_NUMBER), 400))

                list_center_zone = CenterFacade.get_all_zones_name(center_name)

                global_identities_ids = [
                    global_identity["global_identity"]
                    for global_identity in global_identities
                ]

                dwell_query = DwellTime.objects(
                    center_name=center_name,
                    global_identity__in=global_identities_ids,
                    area__in=list_center_zone,
                    epoch_second__gte=int(from_time),
                    epoch_second__lte=int(to_time),
                ).all()
                list_dwell = [
                    (
                        dwell.center_name,
                        dwell.epoch_second,
                        dwell.global_identity,
                        dwell.dwell_time,
                    )
                    for dwell in dwell_query
                ]

                df_dwell_db = pd.DataFrame(
                    list_dwell,
                    columns=[
                        "center_name",
                        "epoch_second",
                        "global_identity",
                        "dwell_time",
                    ],
                ).dropna()

                df_dwell_sum = (
                    df_dwell_db[["global_identity", "dwell_time"]]
                    .groupby(["global_identity"], as_index=False)
                    .sum()
                )

                response_list = []
                areas = Areas.objects(center_name=center_name).all()
                list_areas_highlight = [
                    {
                        "area_name": area.area_name,
                        "area_type": area.area_type,
                        "highlight_on_customers": area.highlight_on_customers,
                    }
                    for area in areas
                    if all(area) and area.highlight_on_customers is not None
                ]

                for customer in global_identities[
                    page * page_size : page * page_size + page_size
                ]:
                    list_highlight_on_customers = []
                    list_process_area_type = []
                    for area in list_areas_highlight:
                        if (
                            area["highlight_on_customers"] == area_highlight_type
                            and area["area_type"] not in list_process_area_type
                        ):
                            df_area = df_db[
                                (
                                    df_db["global_identity"]
                                    == customer["global_identity"]
                                )
                                & (df_db["area_type"] == area["area_type"])
                            ]
                            list_highlight_on_customers.append(
                                {
                                    "area_name": area["area_type"],
                                    "value": len(df_area) > 0,
                                }
                            )
                            list_process_area_type.append(area["area_type"])
                        elif area["highlight_on_customers"] == area_highlight_name:
                            df_area = df_db[
                                (
                                    df_db["global_identity"]
                                    == customer["global_identity"]
                                )
                                & (df_db["area_type"] == area["area_type"])
                                & (df_db["area"] == area["area_name"])
                            ]
                            list_highlight_on_customers.append(
                                {
                                    "area_name": area["area_name"],
                                    "value": len(df_area) > 0,
                                }
                            )

                    if is_live:
                        df_happiness_global_identity = df_db[
                            df_db["global_identity"] == customer["global_identity"]
                        ]
                        global_identity_epoch = df_happiness_global_identity[
                            "epoch_second"
                        ].iloc[0]

                    else:
                        latest_epoch_second = df_db[
                            df_db["global_identity"] == customer["global_identity"]
                        ]["epoch_second"].max()

                        df_happiness_global_identity = df_db[
                            (df_db["global_identity"] == customer["global_identity"])
                            & (df_db["epoch_second"] == latest_epoch_second)
                        ]
                        global_identity_epoch = latest_epoch_second

                    age = df_happiness_global_identity["age"].iloc[0]
                    happiness = df_happiness_global_identity["happiness"].iloc[0]
                    gender = df_happiness_global_identity["gender"].iloc[0]
                    ethnicity = df_happiness_global_identity["ethnicity"].iloc[0]

                    if pd.isna(happiness):
                        happiness = 0

                    if len(df_dwell_sum) > 0:
                        df_dwell_global = df_dwell_sum[
                            df_dwell_sum["global_identity"]
                            == customer["global_identity"]
                        ]

                        if len(df_dwell_global) > 0:
                            if is_live == True:
                                df_customer_tracker = df_db[
                                    df_db["global_identity"]
                                    == customer["global_identity"]
                                ]
                                time_passed = df_customer_tracker[
                                    "live_dwell_time"
                                ].iloc[0]
                                dwell_time = (
                                    df_dwell_global["dwell_time"].iloc[0] + time_passed
                                )

                            else:
                                dwell_time = df_dwell_global["dwell_time"].iloc[0]
                        else:
                            dwell_time = 0
                    else:
                        dwell_time = 0

                    response_list.append(
                        {
                            "id": customer["global_identity"],
                            "epoch_second": int(global_identity_epoch),
                            "dwell_time": dwell_time,
                            "gender": gender,
                            "age": age,
                            "ethnicity": ethnicity,
                            "happiness": float(happiness),
                            "highlight_on_customers_areas": list_highlight_on_customers,
                        }
                    )
                response_list.sort(
                    key=CenterFacade.takeCustomerEpochSecond, reverse=True
                )

            return {
                "total_customers": total_customers,
                "total_pages": total_pages,
                "customers": response_list,
            }

        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_center_area_statistics(center_name, from_time, to_time, is_live):
        if (
            center_name is None
            or from_time is None
            or to_time is None
            or is_live is None
            or from_time > to_time
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                areas = Areas.objects(center_name=center_name).all()
                encoding = "utf-8"

                list_areas = [
                    {
                        "center_name": area.center_name,
                        "area_name": area.area_name,
                        "area_type": area.area_type,
                        "polygon": area.polygon.decode(encoding),
                        "clients": 0,
                    }
                    for area in areas
                    if all(area)
                ]

                list_areas_entrance = [
                    area.area_name
                    for area in areas
                    if all(area)
                    and (
                        area.area_type == entry_area_type
                        or area.area_type == exit_area_type
                    )
                ]

                if is_live:
                    customers = CustomerTracker.objects(center_name=center_name).all()
                    list_timelines = [
                        (
                            timeline.center_name,
                            timeline.global_identity,
                            timeline.area,
                            timeline.area_type,
                        )
                        for timeline in customers
                        if all(timeline)
                    ]
                else:
                    customers = Timeline.objects(
                        center_name=center_name,
                        epoch_second__gte=int(from_time),
                        epoch_second__lte=int(to_time),
                    ).all()
                    list_timelines = [
                        (
                            timeline.center_name,
                            timeline.global_identity,
                            timeline.area,
                            timeline.area_type,
                        )
                        for timeline in customers
                        if all(timeline)
                    ]
                df_db = pd.DataFrame(
                    list_timelines,
                    columns=["center_name", "global_identity", "area", "area_type"],
                ).dropna()
                if len(df_db) <= 0:
                    return {"clients": 0, "areas": list_areas}

                global_identities = list(df_db["global_identity"].unique())
                total_global_identities = len(global_identities)
                total_entrance_identities = 0

                for area in list_areas:
                    df_area = df_db[df_db["area"] == area["area_name"]]
                    area["clients"] = len(list(df_area["global_identity"].unique()))
                    if (
                        area["area_type"] == entry_area_type
                        or area["area_type"] == exit_area_type
                    ):
                        total_entrance_identities += area["clients"]

                if is_live:
                    customers = DwellTime.objects(
                        center_name=center_name,
                        global_identity__in=global_identities,
                        area__in=list_areas_entrance,
                        epoch_second__gte=int(from_time),
                        epoch_second__lte=int(to_time),
                    ).all()
                    list_timelines = [
                        (timeline.center_name, timeline.global_identity, timeline.area)
                        for timeline in customers
                        if all(timeline)
                    ]

                    df_db = pd.DataFrame(
                        list_timelines,
                        columns=["center_name", "global_identity", "area"],
                    ).dropna()
                    if len(df_db) <= 0:
                        if total_entrance_identities < total_global_identities:
                            for area in list_areas:
                                if (
                                    area["area_type"] == entry_area_type
                                    and area["area_name"] == default_entrance_area
                                ):
                                    area["clients"] += (
                                        total_global_identities
                                        - total_entrance_identities
                                    )
                        return {"clients": total_global_identities, "areas": list_areas}
                    total_entrance_identities = 0
                    for area in list_areas:
                        if (
                            area["area_type"] == entry_area_type
                            or area["area_type"] == exit_area_type
                        ):
                            df_area = df_db[df_db["area"] == area["area_name"]]
                            area["clients"] = len(
                                list(df_area["global_identity"].unique())
                            )
                            total_entrance_identities += area["clients"]

                # By Default: if clients not detected in any
                if total_entrance_identities < total_global_identities:
                    for area in list_areas:
                        if (
                            area["area_type"] == entry_area_type
                            and area["area_name"] == default_entrance_area
                        ):
                            area["clients"] += (
                                total_global_identities - total_entrance_identities
                            )

                return {"clients": total_global_identities, "areas": list_areas}
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_center_area_dwell_statistics(center_name, from_time, to_time):
        if (
            center_name is None
            or from_time is None
            or to_time is None
            or from_time > to_time
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                areas = Areas.objects(center_name=center_name).all()
                encoding = "utf-8"
                list_areas = [
                    {
                        "center_name": area.center_name,
                        "area_name": area.area_name,
                        "area_type": area.area_type,
                        "polygon": area.polygon.decode(encoding),
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

                df_dwell = df_db.groupby("area", as_index=False).mean()
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
    def get_customer_journey(center_name, global_identity):
        if center_name is None or global_identity is None:
            abort(make_response(jsonify(error=NULL_PARAMS), 400))

        try:
            center_exist = Center.objects(name=center_name).get()
            if center_exist:
                areas = Areas.objects(center_name=center_name).all()
                areas_type = {}

                for area in areas:
                    if all(area):
                        areas_type[area.area_name] = area.area_type

                customers = DwellTime.objects(
                    center_name=center_name, global_identity=global_identity
                ).all()

                list_dwell = [
                    {
                        "area_name": timeline.area,
                        "epoch_second_entrance": int(
                            timeline.epoch_second - int(timeline.dwell_time)
                        ),
                        "dwell_time": timeline.dwell_time,
                        "avg_hx": 0.0,
                    }
                    for timeline in customers
                    if all(timeline)
                ]
                min_epoch_second = 0
                max_epoch_second = 0
                for area in list_dwell:
                    if area["area_name"] in areas_type:
                        area["area_type"] = areas_type[area["area_name"]]
                    else:
                        area["area_type"] = "null"
                    if (
                        min_epoch_second == 0
                        or area["epoch_second_entrance"] < min_epoch_second
                    ):
                        min_epoch_second = area["epoch_second_entrance"]
                    if (
                        max_epoch_second == 0
                        or (area["epoch_second_entrance"] + int(area["dwell_time"]))
                        > max_epoch_second
                    ):
                        max_epoch_second = area["epoch_second_entrance"] + int(
                            area["dwell_time"]
                        )

                customers = Timeline.objects(
                    center_name=center_name,
                    epoch_second__gte=int(min_epoch_second),
                    epoch_second__lte=int(max_epoch_second),
                ).all()

                list_timelines = [
                    (timeline.epoch_second, timeline.area, timeline.happiness,)
                    for timeline in customers
                    if all(timeline) and timeline.global_identity == global_identity
                ]

                df_db = pd.DataFrame(
                    list_timelines, columns=["epoch_second", "area", "happiness"],
                ).dropna()

                if len(df_db) <= 0:
                    list_dwell.sort(key=CenterFacade.takeCustomerJourneyEpochSecond)
                    return list_dwell

                for area in list_dwell:
                    epoch_second_exit = area["epoch_second_entrance"] + int(
                        area["dwell_time"]
                    )
                    df_area = df_db[
                        (df_db["epoch_second"] >= area["epoch_second_entrance"])
                        & (df_db["epoch_second"] <= epoch_second_exit)
                        & (df_db["area"] == area["area_name"])
                    ]
                    if len(df_area) > 0:
                        df_happiness = (
                            df_area[["area", "happiness"]]
                            .groupby("area", as_index=False)
                            .mean()
                        )
                        area["avg_hx"] = float(df_happiness["happiness"].iloc[0])

                list_dwell.sort(key=CenterFacade.takeCustomerJourneyEpochSecond)
                return list_dwell
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))

    @staticmethod
    def get_waiting_demographics(center, from_time, to_time, is_live):
        if (
            center is None
            or from_time is None
            or to_time is None
            or is_live is None
            or from_time > to_time
        ):
            abort(make_response(jsonify(error=NULL_PARAMS), 400))
        try:
            center_exists = Center.objects(name=center).get()
        except cassandra.cqlengine.query.DoesNotExist:
            abort(make_response(jsonify(error=CENTER_NOT_FOUND), 400))
        if center_exists:
            if is_live:
                customers = CustomerTracker.objects(center_name=center).all()
            else:
                customers = Timeline.objects(
                    center_name=center,
                    epoch_second__gte=from_time,
                    epoch_second__lte=to_time,
                ).all()
            waiting_customers = [
                customer for customer in customers if customer.area_type == "Waiting"
            ]
            checked_id_list = []
            response = {
                "Male": 0,
                "Female": 0,
                "Local": 0,
                "Non": 0,
                "POD": 0,
            }
            for customer in waiting_customers:
                if customer.global_identity not in checked_id_list:
                    checked_id_list.append(customer.global_identity)
                    if customer.gender is not None:
                        response[customer.gender] += 1
                    if customer.ethnicity is not None:
                        response[customer.ethnicity] += 1
            return response

