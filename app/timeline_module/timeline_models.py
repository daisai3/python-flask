from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Timeline(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "128",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_data"
    center_name = columns.Text(partition_key=True)
    epoch_second = columns.BigInt(primary_key=True, required=True)
    global_identity = columns.Text(primary_key=True, required=True)

    area = columns.Text(required=True)
    area_type = columns.Text()
    position_x = columns.Integer()
    position_y = columns.Integer()

    age = columns.Text()
    gender = columns.Text()
    ethnicity = columns.Text()
    happiness = columns.Integer()
    face_crop = columns.Blob()
    mask = columns.Text()


class CustomerTracker(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "128",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_data"
    center_name = columns.Text(partition_key=True)
    global_identity = columns.Text(primary_key=True, required=True)
    area = columns.Text(required=True)
    epoch_second = columns.BigInt(required=True)

    area_type = columns.Text()
    position_x = columns.Integer(required=True)
    position_y = columns.Integer(required=True)
    live_dwell_time = columns.BigInt()
    age_range = columns.Text()
    gender = columns.Text()
    ethnicity = columns.Text()
    happiness_index = columns.Integer()
    mask = columns.Text()


class DwellTime(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "128",
            "tombstone_threshold": ".2",
        },
        "comment": "User data stored here",
    }
    __keyspace__ = "cja_data"
    center_name = columns.Text(partition_key=True, required=True)
    global_identity = columns.Text(primary_key=True, required=True)
    area = columns.Text(primary_key=True, required=True)
    epoch_second = columns.Decimal(primary_key=True, required=True)
    dwell_time = columns.Float(primary_key=True, required=True)
