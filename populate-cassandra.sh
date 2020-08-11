docker exec  -it $1  rm -rf test-db
docker cp ./app/test_config/test-db $1:/app/test_config/test-db/
echo "File copied"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_metadata.calibration (center_name, camera_id, calibration_info) FROM './app/test_config/test-db/calibration.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_metadata.language (iso_string, name) FROM './app/test_config/test-db/language.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_metadata.working_hours (type) FROM './app/test_config/test-db/working_hours.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_metadata.user_status (status) FROM './app/test_config/test-db/user_status.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_metadata.areas (center_name, area_type, area_name, polygon, highlight_on_customers) FROM './app/test_config/test-db/areas.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_data.user (email, center_name, designated_zone_name, gender, hashed_pass, is_active, job_title, language, name, phone, photo, role, salt, working_hours) FROM './app/test_config/test-db/user.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_data.users_by_location (center_name, email, designated_zone_name, is_active, job_title, language, name, photo, role, working_hours) FROM './app/test_config/test-db/user_by_location.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_data.timeline (center_name, global_identity, epoch_second, age, area, area_type, ethnicity, face_crop, gender, happiness, mask, position_x, position_y) FROM './app/test_config/test-db/timeline.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_data.customer_tracker (center_name, global_identity, age_range, live_dwell_time, area, area_type, epoch_second, ethnicity, gender, happiness_index, mask, position_x, position_y) FROM './app/test_config/test-db/customer_tracker.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_data.center (name, distance_points, floor_plan, floor_plan_px_per_meter, lat, lng, location, manager_email, manager_name, scale_meters) FROM './app/test_config/test-db/centers.dat';"
docker exec -it $1 cqlsh localhost -u cassandra -p cassandra -e "COPY cja_data.dwell_time (center_name, global_identity, area,  epoch_second, dwell_time) FROM './app/test_config/test-db/dwell_time.dat';"
