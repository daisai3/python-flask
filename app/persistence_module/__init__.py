from cassandra.cqlengine.management import sync_table, create_keyspace_simple
from cassandra.cqlengine import connection
from cassandra.query import dict_factory
from cassandra.auth import PlainTextAuthProvider
from app.center_module.center_models import Center, Areas
import logging
import cassandra
import os
import time
import json
import sys

# from .highlights_facade import Highlight
from app.user_module.user_models import (
    User,
    UsersByLocation,
    UserStatus,
    Language,
    WorkingHours,
)

from app.calibration_module.calibration_models import Calibration
from app.timeline_module.timeline_models import Timeline, CustomerTracker, DwellTime


class Persistence:
    def __init__(self):
        cass_user = os.getenv("DB_USER", "cassandra")
        cass_passwd = os.getenv("DB_PASSWORD", "cassandra")
        host = os.getenv("DB_URI", "localhost")
        port = int(os.getenv("DB_PORT", 9042))
        auth_provider = PlainTextAuthProvider(username=cass_user, password=cass_passwd)

        while True:
            try:
                connection.setup(
                    hosts=[host],
                    port=port,
                    default_keyspace="cja",
                    protocol_version=4,
                    auth_provider=auth_provider,
                )
                break
            except cassandra.AuthenticationFailed as e:
                logging.error(f"{e}\nExiting")
                sys.exit(9)
            except cassandra.cluster.NoHostAvailable as e:
                logging.warning(f"{e}\nRetrying")
                time.sleep(10)
            except Exception as e:
                logging.info(f"{e}\nRetrying...")
                time.sleep(10)

        connection.get_session().row_factory = dict_factory

        self.connection = connection.get_session()

    def create_schema(self):
        create_keyspace_simple(name="cja_metadata", replication_factor=1)
        create_keyspace_simple(name="cja_data", replication_factor=1)
        sync_table(Center)
        sync_table(Areas)
        sync_table(User)
        sync_table(UsersByLocation)
        sync_table(WorkingHours)
        sync_table(UserStatus)
        sync_table(Language)
        sync_table(Timeline)
        sync_table(CustomerTracker)
        sync_table(Calibration)
        sync_table(DwellTime)

        return self
