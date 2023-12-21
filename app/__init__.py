import locale
import logging
from datetime import datetime
from pythonjsonlogger import jsonlogger

from flask import Flask
from flask_cors import CORS

import config as cf

app = Flask(__name__)
CORS(app)

locale.setlocale(locale.LC_ALL, cf.locale_choice)  # to sort æøå correctly
app.config['JSON_AS_ASCII'] = cf.set_json_as_ascii
app.config['JSON_SORT_KEYS'] = cf.sort_json_keys


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(
            log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


logger = logging.getLogger(__name__)
log_handler = logging.StreamHandler()
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
log_handler.setFormatter(formatter)
logger.addHandler(log_handler)
logger.setLevel(cf.logging_level)

from app import routes
