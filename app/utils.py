
import re
import logging

from flask import jsonify, abort


logger = logging.getLogger(__name__)


def return_jsonify_dump(outSchema, outDict, many=False):
    try:
        to_jsonify = outSchema.dump(outDict, many=many)
        logger.info(f'Output size after schema dumping: {to_jsonify.__sizeof__()}')
        logger.debug(f'Final output after schema dumping: {to_jsonify}')
        return jsonify(to_jsonify)
    except KeyError as e:
        logger.warning(f'Error occured when dumping data to schema:\n{e}')
        abort(400, 'Mulig feil i parameter')
    except ValueError as e:
        logger.warning(f'ValueError occured when dumping data to schema:\n{e}')
        abort(400, 'Mulig feil i filtreringsparameter')


def create_geojson_output(data, geojson_element, srid):
    hits = []
    for hit in data:
        gj = {"type": "Feature",
              "geometry": hit.get(geojson_element),
              "properties": hit}
        hits.append(gj)
    if srid not in (4326, 4258):
        geojson_out = {'type': "FeatureCollection",
                       "crs": {
                           "properties": {"name": f"EPSG:{srid}"},
                           "type": "name"
                       },
                       "features": hits}
    else:
        geojson_out = {'type': "FeatureCollection", "features": hits}
    logger.info(f'Created geojson output: {geojson_out}')
    return geojson_out


def format_metadata_output(data, page, hits_per_page, search_string):
    if data:
        num_of_hits = data[0]['result_count']
    else:
        num_of_hits = 0
    outDict = {'metadata': {'treffPerSide': hits_per_page,
                            'side': page,
                            'totaltAntallTreff': num_of_hits,
                            'viserFra': 1 + (page * hits_per_page) - hits_per_page,
                            'viserTil': page * hits_per_page,
                            'sokeStreng': search_string},
               'eiendom': data}
    logger.info(f'Formatted metadata output: {outDict["metadata"]}')
    return outDict


def deserialize_input_params(inputParams, modelObj):
    """
    inputParams should be a dict.
    modelObj should be a marshmallow model
    """
    logger.info('input params to deserialize: %s' % inputParams)
    try:
        deserializedParams = modelObj.load(inputParams)
    except Exception as e:
        logger.error(e)
        abort(400, e.messages)
    logger.info('deserializedParams:  \n %s' % deserializedParams)
    return deserializedParams


def filter_model(modelMa, filterDict):
    try:
        return modelMa(**filterDict)
    except Exception as e:
        logger.warning(f'Error occured when trying to filter the model:\n {e}')
        abort(400, "Feil i filtreringsparameter. Husk på at underelementer må spesifiseres slik: filtrer=metadata.side")


def create_filtering_dict(filterInput):
    if filterInput:
        inclDict = {'only': filterInput.split(',')}
    else:
        inclDict = {}
    logger.debug('filtering Dict: %s' % inclDict)
    return inclDict


def try_to_get_value_from_arg(args, arg_name):
    try:
        return args[arg_name]
    except Exception as E:
        logger.debug('No data in argument "%s". Exception: \n%s' % (arg_name, E))
        return None


def decode_query_string(query_string):
    res = query_string.decode('utf8').replace('\\', ' ').replace('%22', '')
    logger.debug(f'Decoded {query_string} to {res}')
    return res


class ConstructSql:

    def __init__(self, args):
        self.kommunenummer = try_to_get_value_from_arg(args, 'kommunenummer')
        self.gardsnummer = try_to_get_value_from_arg(args, 'gardsnummer')
        self.bruksnummer = try_to_get_value_from_arg(args, 'bruksnummer')
        self.festenummer = try_to_get_value_from_arg(args, 'festenummer')
        self.seksjonsnummer = try_to_get_value_from_arg(args, 'seksjonsnummer')
        self._parse_matrikkelnummer(try_to_get_value_from_arg(args, 'matrikkelnummer'))
        self.args = args
        self.queries = []
        self.query_input = []

    def geolokasjon_query(self):
        self._check_required_nummer()
        self._create_kommunenummer_sql()
        self._create_gardsnummer_sql()
        self._create_bruksnummer_sql()
        self._create_festenummer_sql()
        self._create_seksjonsnummer_sql()
        query_where, query_input = self._create_where_query()
        ordering_sql = self._create_ordering_sql()
        query_where += ordering_sql
        return query_where, query_input

    def _create_ordering_sql(self):
        return """ ORDER BY hoved DESC"""

    def _check_required_nummer(self):
        if not self.gardsnummer or not self.bruksnummer or not self.kommunenummer:
            abort(400, 'Man må minst sende inn kommunenummer, gardsnummer og bruksnummer')

    def _create_kommunenummer_sql(self):
        self.queries.append('kommunenummer = %s')
        self.query_input.append(self.kommunenummer)

    def _create_gardsnummer_sql(self):
        self.queries.append('gardsnummer = %s')
        self.query_input.append(self.gardsnummer)

    def _create_bruksnummer_sql(self):
        self.queries.append('bruksnummer = %s')
        self.query_input.append(self.bruksnummer)

    def _create_festenummer_sql(self):
        if not self.festenummer:
            return
        self.queries.append('festenummer = %s')
        self.query_input.append(self.festenummer)

    def _create_seksjonsnummer_sql(self):
        if not self.seksjonsnummer:
            return
        self.queries.append('seksjonsnummer = %s')
        self.query_input.append(self.seksjonsnummer)

    def _create_where_query(self):
        query_where = 'WHERE '
        if not self.queries:
            abort(400, 'Ingen søkeparametere angitt.')
        for index, query_part in enumerate(self.queries):
            if index == 0:
                query_where += query_part
            else:
                query_where += " AND " + query_part
        logger.debug(query_where)
        logger.debug(self.query_input)
        return query_where, tuple(self.query_input)

    def create_pagination_sql(self):
        page = self.args['side']
        hits_per_page = self.args['treffPerSide']
        offset = (page - 1) * hits_per_page
        pagination = """ LIMIT {0} OFFSET {1} """.format(hits_per_page, offset)
        logger.debug(f'Created pagination query: {pagination}')
        return pagination

    def _parse_matrikkelnummer(self, search_param):
        if not search_param:
            return search_param
        search_param = search_param.strip()
        match_pattern = re.compile(r"[0-9/-]+")
        if not re.fullmatch(match_pattern, search_param):
            abort(400, 'Ugyldig(e) tegn i søkeparameteret. Husk på at matrikkelnummer bruker skråstreker /, og ikke bakstreker (omvendt skråstrek) \\.')
        if search_param.count('/') < 1:
            abort(400, 'Mangler skråstrek i matrikkelnummeret etter gardsnummeret.')
        numbers = search_param.split('/')

        try:
            kommunenummer, gardsnummer = numbers[0].split('-')
        except Exception as e:
            logger.warning(e)
            abort(400, 'Feil i matrikkelnummeret, forventer en bindestrek mellom kommunenummer-gardsnummer')
        numbers = [kommunenummer, gardsnummer] + numbers[1:]
        numbers_valid = []
        for index, number in enumerate(numbers):
            try:
                if index == 0:
                    int(number)  # check kommunenummer, but keep as string
                else:
                    number = int(number)
                if number == 0:  # stored as NULL in the database
                    number = None
                numbers_valid.append(number)
            except Exception as e:
                logger.warning(e)
                abort(400, f'Feil i matrikkelnummeret: {search_param}')

        num_elements = len(numbers_valid)
        if num_elements < 3:
            abort(400, 'For få elementer i matrikkelnummeret. Må ha med minst kommunenummer, gardsnummer og bruksnummer.')
        self.kommunenummer = numbers_valid[0].strip()
        self.gardsnummer = numbers_valid[1]
        self.bruksnummer = numbers_valid[2]
        if num_elements > 3 and numbers_valid[3]:
            self.festenummer = numbers_valid[3]
        if num_elements > 4 and numbers_valid[4]:
            self.seksjonsnummer = numbers_valid[4]
