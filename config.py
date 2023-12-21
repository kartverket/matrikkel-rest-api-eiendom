import os

db_user = os.environ.get('EIENDOM_DB_USER', default='eiendom')
db_password = os.environ.get('EIENDOM_DB_PASSWORD', default="eiendom")
db_uri = os.environ.get('EIENDOM_DB_URI',
                        default="postgresql://localhost:5432/eiendom")
app_ingress = os.environ.get("EIENDOM_INGRESS", default="localhost:5000")
logging_level = os.environ.get('EIENDOM_API_LOG_LEVEL', 'ERROR')

is_dev = True if app_ingress == "localhost:5000" else False
set_json_as_ascii = False
locale_choice = 'no_NO.UTF-8'
sort_json_keys = False

db_srid = 4258
