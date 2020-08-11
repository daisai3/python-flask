from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Center(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "64",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_data"
    name = columns.Text(primary_key=True, required=True)
    location = columns.Text(required=True)
    lng = columns.Float(required=True)
    lat = columns.Float(required=True)
    manager_name = columns.Text(required=True)
    manager_email = columns.Text(required=True)
    floor_plan = columns.Bytes()
    scale_meters = columns.Float()
    distance_points = columns.Bytes()
    floor_plan_px_per_meter = columns.Float()


class Areas(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "64",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_metadata"
    center_name = columns.Text(partition_key=True, required=True)
    area_type = columns.Text(primary_key=True, required=True)
    area_name = columns.Text(primary_key=True, required=True)
    polygon = columns.Bytes(required=True)
    highlight_on_customers = columns.Text()
