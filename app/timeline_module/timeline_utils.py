import base64

area_positions = {"Entry": 0, "Support": 1, "Waiting": 2, "Interaction": 3, "Exit": 4}

gender_values = ["Male", "Female"]
ethnicity_values = ["Local", "Nonlocal"]
age_values = ["0-18", "19-49", "50+"]
history_type_values = ["attendance", "happiness"]


def sortByArea(element):
    return area_positions[element["area_type"]]


def stage_timeline_mapper(frame):
    return {
        "timestamp": frame.epoch_second,
        "type": frame.area_type,
        "value": frame.area,
    }


def happiness_timeline_mapper(frame):
    return {"timestamp": frame.epoch_second, "value": frame.happiness}


def footage_timeline_mapper(frame):
    crop_blob = frame.face_crop
    if crop_blob is not None:
        base64_crop = base64.b64encode(crop_blob)
        decoded_crop = base64_crop.decode("utf-8")
        return {"timestamp": frame.epoch_second, "value": decoded_crop}
    return None


def history_happiness_mapper(
    epoch_interval, time_interval, df_gender, df_ethnicity, df_grouped_age
):
    epoch_interval_dict = {}
    epoch_interval_dict["time"] = int(epoch_interval * time_interval)
    for index, row in df_gender.iterrows():
        epoch_interval_dict[row["gender"]] = round(row["happiness"])
    for gender_value in gender_values:
        if gender_value not in epoch_interval_dict:
            epoch_interval_dict[gender_value] = 0
    for index, row in df_ethnicity.iterrows():
        epoch_interval_dict[row["ethnicity"]] = round(row["happiness"])
    for ethnicity_value in ethnicity_values:
        if ethnicity_value not in epoch_interval_dict:
            epoch_interval_dict[ethnicity_value] = 0

    for index, row in df_grouped_age.iterrows():
        epoch_interval_dict[row["age"]] = round(row["happiness"])
    for age_value in age_values:
        if age_value not in epoch_interval_dict:
            epoch_interval_dict[age_value] = 0

    if epoch_interval_dict["Female"] == 0:
        epoch_interval_dict["total_avg"] = epoch_interval_dict["Male"]
    elif epoch_interval_dict["Male"] == 0:
        epoch_interval_dict["total_avg"] = epoch_interval_dict["Female"]
    else:
        epoch_interval_dict["total_avg"] = (
            epoch_interval_dict["Male"] + epoch_interval_dict["Female"]
        ) / 2

    return epoch_interval_dict
