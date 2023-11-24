import os

database = 'matrikkeleneiendom'
user = 'dbles'
port = 5432
host = os.environ.get('EIENDOM_DB_HOST')
password = os.environ.get('PG_PASS_EIENDOM')


dbc = {'database': database, 'user': user, 'port': port, 'host': host, 'password': password}

set_json_as_ascii = False
locale_choice = 'no_NO.UTF-8'
logging_level = os.environ.get('EIENDOM_API_LOG_LEVEL', 'ERROR')
sort_json_keys = False

db_srid = 4258
