FROM python:3.9-alpine
ADD . /app
WORKDIR /app
RUN pip install pipenv && pipenv install
CMD sh docker-entrypoint.sh