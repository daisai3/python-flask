#!/bin/bash

parent_path=$( cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd -P )
cd $parent_path

docker-compose -f ./app/test_config/docker-compose.yml up -d --build --force-recreate

echo 'Waiting for API server to be up...'
response=0
while [ $response != 200 ]
do
  response=$(curl --write-out %{http_code} --silent --output /dev/null http://localhost:5000/status)
  echo ${response}
  if [ $response != 200 ]
  then
    sleep 3
  fi
done

./populate-cassandra.sh tessandra

echo Running Tests for $(pwd)...
docker exec -it cja-backend-testing pytest app
test_exit_code=$?

docker-compose -f ./app/test_config/docker-compose.yml down

if [ $test_exit_code == 1 ]
then
  echo Tests failed
  exit 1
fi
echo Done