import datetime
import logging
import sys
import config as cf

import json_log_formatter

workers = 1
worker_connections = 1000
timeout = 30
keepalive = 2
threads = 4
bind = '0.0.0.0:5000'
accesslog = "-"  # Logs to stdout
errorlog = "-"  # Logs to stdout


# Formatter taken from this article: https://til.codeinthehole.com/posts/how-to-get-gunicorn-to-log-as-json/
# As recommended by this Gunicorn GitHub issue:
class JsonRequestFormatter(json_log_formatter.JSONFormatter):
    def json_record(
        self,
        message: str,
        extra: dict[str, str | int | float],
        record: logging.LogRecord
    ) -> dict[str, str | int | float]:
        # Convert the log record to a JSON object.
        # See https://docs.gunicorn.org/en/stable/settings.html#access-log-format

        response_time = datetime.datetime.strptime(
            record.args["t"], "[%d/%b/%Y:%H:%M:%S %z]"
        )
        url = record.args["U"]
        if record.args["q"]:
            url += f"?{record.args['q']}"

        return dict(
            remote_ip=record.args["h"],
            method=record.args["m"],
            path=url,
            status=str(record.args["s"]),
            time=response_time.isoformat(),
            user_agent=record.args["a"],
            referer=record.args["f"],
            duration_in_ms=record.args["M"],
            pid=record.args["p"],
        )


class JsonErrorFormatter(json_log_formatter.JSONFormatter):
    def json_record(
        self,
        message: str,
        extra: dict[str, str | int | float],
        record: logging.LogRecord
    ) -> dict[str, str | int | float]:
        payload: dict[str, str | int | float] = super().json_record(
            message, extra, record
        )
        payload["level"] = record.levelname
        return payload


is_dev = cf.is_dev
# Ensure the two named loggers that Gunicorn uses are configured to use a custom
# JSON formatter.
if not is_dev:
    logconfig_dict = {
        "version": 1,
        "formatters": {
            "json_request": {
                "()": JsonRequestFormatter,
            },
            "json_error": {
                "()": JsonErrorFormatter,
            },
        },
        "handlers": {
            "json_request": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json_request",
            },
            "json_error": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json_error",
            },
        },
        "root": {"level": "INFO", "handlers": []},
        "loggers": {
            "gunicorn.access": {
                "level": "INFO",
                "handlers": ["json_request"],
                "propagate": False,
            },
            "gunicorn.error": {
                "level": "INFO",
                "handlers": ["json_error"],
                "propagate": False,
            },
        },
    }
