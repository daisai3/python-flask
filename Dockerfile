FROM python:3.6

RUN python --version
RUN pip --version

COPY ./requirements.txt /requirements.txt

RUN pip install -r requirements.txt

COPY . ./
ENV FLASK_RUN_HOST 0.0.0.0
ENV FLASK_ENV=development
ENTRYPOINT [ "flask", "run"]