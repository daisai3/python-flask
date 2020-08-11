from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class User(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "128",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_data"
    email = columns.Text(required=True, primary_key=True)
    center_name = columns.Text(required=True)
    working_hours = columns.Text(required=True)
    is_active = columns.Text(required=True)
    name = columns.Text(required=True)
    job_title = columns.Text(required=True)
    designated_zone_name = columns.Text()
    language = columns.Text(required=True)
    role = columns.Text(required=True)
    gender = columns.Text()
    photo = columns.Blob()
    phone = columns.Text()
    hashed_pass = columns.Text(required=True)
    salt = columns.Text(required=True)


class UsersByLocation(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "128",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_data"
    center_name = columns.Text(required=True, partition_key=True)
    email = columns.Text(required=True, primary_key=True)
    working_hours = columns.Text(required=True,)
    is_active = columns.Text(required=True)
    photo = columns.Blob()
    name = columns.Text(required=True)
    job_title = columns.Text(required=True)
    designated_zone_name = columns.Text()
    language = columns.Text(required=True)
    role = columns.Text(required=True)


class WorkingHours(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "64",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_metadata"
    type = columns.Text(primary_key=True, required=True)


class UserStatus(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "64",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_metadata"
    status = columns.Text(primary_key=True, required=True)


class Language(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "64",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_metadata"
    iso_string = columns.Text(primary_key=True, required=True)
    name = columns.Text(required=True)
