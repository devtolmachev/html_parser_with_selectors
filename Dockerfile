FROM python:3.13-alpine

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install poetry

COPY pyproject.toml .

RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

COPY . .

ENV PYTHONPATH=/app
CMD poetry run python html_parser_with_selectors/api.py
