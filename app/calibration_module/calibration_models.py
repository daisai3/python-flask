from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns


class Calibration(Model):
    __options__ = {
        "compaction": {
            "class": "LeveledCompactionStrategy",
            "sstable_size_in_mb": "64",
            "tombstone_threshold": ".2",
        }
    }
    __keyspace__ = "cja_metadata"
    center_name = columns.Text(primary_key=True, required=True)
    camera_id = columns.Text(primary_key=True, required=True)
    # floor_coords
    # camera_coords
    # calibration_matrix
    # camera_position
    # cameraRTSP
    # encoding
    # focal_length
    # resolution
    calibration_info = columns.Bytes(required=True)
