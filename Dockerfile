FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip3 install pipenv

# -- Adding Pipfiles
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

# -- Install dependencies:
RUN set -ex && pipenv install --deploy --system

COPY ./app /app