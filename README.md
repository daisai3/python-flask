# Customer Journey Analytics API

Api backend to serve CJA frontend with data from CassandraDB

Based using Python's [Flask](https://flask.palletsprojects.com/en/1.1.x/) framework.

### Documentation

Once you got the API running you could go to http://localhost:5000/documentation

### Dockerized App

Take into consideration that the Cassandra container used by the cja-engine must be up and in the same docker network:

You should also have the frontend repository in the same root folder:

cja/ ├── cja-dashboard └── cja-api-backend

You can find **cja-dashboard** [here](https://gitlab.com/dive.tv/cja/cja-dashboard)

To start both containers run on the cja-api-backend:

`docker-compose -f docker-compose.yml up --build`

After building the containers, if you are on a dev environment, you can fill in the db with dummy data running

`./populate-cassandra.sh {container-name}`

If running on smaug, you must forward port 3000 for the frontend and port 5000 for the backend

####Start on local

Activate Venv:

`source ./venv/bin/activate`

Create a new virtual environment with Python3 and pip if you dont have one. Then install the dependencies with:

`pip install -r requirements.txt`

###Commands:

To Start CQLSH with python 3.6.9: `Env var -> CQLSH_NO_BUNDLED=true` `cqlsh {IP}` (defaults to localhost if no ip is provided)

**To start the API server:**

You should set this Environment Variables for the API to work correctly:

      - AUTH_SECRET={SECRET KEY}
      - CQLENG_ALLOW_SCHEMA_MANAGEMENT=TRUE
      - DB_USER
      - DB_PASSWORD
      - DB_URI
      - DB_PORT

IP address defaults to localhost

After setting these up, run:

`flask run`

And the API will be listening on port 3000

#### Running tests (must be done with bash):

`bash test.sh`
