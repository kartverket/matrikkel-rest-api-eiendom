import locale
import logging

from flask import Flask
from flask_cors import CORS

import config as cf

app = Flask(__name__)
CORS(app)

locale.setlocale(locale.LC_ALL, cf.locale_choice)  # to sort æøå correctly
app.config['JSON_AS_ASCII'] = cf.set_json_as_ascii
app.config['JSON_SORT_KEYS'] = cf.sort_json_keys

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s',
                    level=logging.getLevelName(cf.logging_level))

from app import routes
