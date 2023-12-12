#!/usr/bin/env python3

import logging

from flask import request, jsonify, render_template
from prometheus_flask_exporter import PrometheusMetrics
from webargs.flaskparser import use_args

from app import app
from app import models as md
from app import database as db
from app import apispec_generate
from app import utils as ut


logger = logging.getLogger(__name__)


class PrefixMiddleware(object):
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This route does not exist.".encode()]


metrics = PrometheusMetrics(app)

app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix='/eiendom/v1')

# Return validation errors as JSON


@app.errorhandler(422)
@app.errorhandler(400)
def handle_error(err):
    exc = getattr(err, "exc", None)
    if exc:
        headers = err.data["headers"]
        messages = {'message': exc.messages}
    else:
        headers = None
        messages = {'message': err.description}
    if headers:
        return {"errors": messages}, err.code, headers
    else:
        return {"errors": messages}, err.code


@app.route('/geokoding')
@use_args(md.InputEiendomSchema(), location="query")
def sok_eiendom(args):
    """
    ---
    get:
        summary: Finn representasjonspunkt eller område for et spesifikt matrikkelnummer.
        description: Finn representasjonspunkt eller område for et spesifikt matrikkelnummer. Matrikkelnummeret må ha formen "Kommunenr-Gårdsnr/Bruksnr/Festenr/Seksjonsnr" hvis festenr og seksjonsnr er aktuelt (seksjoner med eget uteareal, eller eiendommen den er seksjonert på). For eksempel ?matrikkelnummer=0301-223/60/0/3<p> Alternativt kan man oppgi nummerene individuelt. For eksempel  ?kommunenummer=0301&gardsnummer=223&bruksnummer=60</p>
        parameters:
            - in: query
              schema: InputEiendomSchema
        responses:
            200:
                description: ok
                content:
                    application/json:
                        schema: GeoKodingRespons
    """
    logger.info(args)
    _ = ut.deserialize_input_params(args, md.InputEiendomSchema())
    teig = ut.try_to_get_value_from_arg(args, 'omrade')
    filtrer = ut.try_to_get_value_from_arg(args, 'filtrer')
    filters = ut.create_filtering_dict(filtrer)
    return_srid = ut.try_to_get_value_from_arg(args, 'utkoordsys')
    logger.debug('Search parameters: %s' % request.args.to_dict())
    query_where, query_input = ut.ConstructSql(args).geolokasjon_query()
    query = db.Queries(return_srid).eiendom_sok(teig=teig, where=query_where)
    output = db.DbConn().perform_query_format_response(query, query_input)
    # if a seksjonsnummer lacks geometry, get it from the property which "owns" it
    if not output and 'seksjonsnummer' in query_where.lower():
        construct_sql = ut.ConstructSql(args)
        construct_sql.seksjonsnummer = None
        query_where, query_input = construct_sql.geolokasjon_query()
        query = db.Queries(return_srid).eiendom_sok(
            teig=teig, where=query_where)
        output = db.DbConn().perform_query_format_response(query, query_input)
    output = ut.create_geojson_output(output, 'rep_geojson', return_srid)

    filterModel = ut.filter_model(md.GeoKodingRespons, filters)

    return ut.return_jsonify_dump(filterModel, output, many=False)


@app.route('/punkt')
@use_args(md.InputPunktSokSchema(), location="query")
def get_eiendom_near_point(args):
    """
    ---
    get:
        summary: Finn eiendommer nær et gitt geografisk punkt.
        description: Gjør et geografisk søk etter de nærmeste eiendommene, dvs deres teiger eller anleggsprojeksjonsflate registrert i matrikkelsystemet. <p>For eksempel ?nord=60.5&ost=11.12&koordsys=4258&radius=1000</p>
        parameters:
            - in: query
              schema: InputPunktSokSchema
        responses:
            200:
                description: ok
                content:
                    application/json:
                        schema: PunktRespons
    """
    _ = ut.deserialize_input_params(args, md.InputPunktSokSchema())
    page = args['side']
    filtrer = ut.try_to_get_value_from_arg(args, 'filtrer')
    return_srid = ut.try_to_get_value_from_arg(args, 'utkoordsys')
    filters = ut.create_filtering_dict(filtrer)
    hits_per_page = args['treffPerSide']
    sql_pagination = ut.ConstructSql(args).create_pagination_sql()
    query = db.Queries(return_srid).eiendom_distance(pagination=sql_pagination)
    radius = args['radius']
    ost, nord = args['ost'], args['nord']
    koordsys = args['koordsys']
    search_string = ut.decode_query_string(request.query_string)
    logger.debug('Search parameters: %s' % request.args.to_dict())
    query_input = ost, nord, koordsys, radius
    output = db.DbConn().perform_query_format_response(query, query_input)
    formatted_output = ut.format_metadata_output(
        output, page, hits_per_page, search_string)
    filterModel = ut.filter_model(md.PunktRespons, filters)
    return ut.return_jsonify_dump(filterModel, formatted_output, many=False)


@app.route('/punkt/omrader')
@use_args(md.InputPunktSokGeojsonSchema(), location="query")
def get_eiendom_teig_near_point(args):
    """
    ---
    get:
        summary: Returnerer GeoJSON med områder nær et gitt geografisk punkt.
        description: Gjør et geografisk søk etter teigene til de nærmeste eiendommene, dvs deres teiger eller anleggsprojeksjonsflate registrert i matrikkelsystemet. Det returneres i form av en GeoJSON-featurecollection. <p>For eksempel ?nord=60.5&ost=11.12&koordsys=4258&radius=1000</p>
        parameters:
            - in: query
              schema: InputPunktSokGeojsonSchema
        responses:
            200:
                description: ok
                content:
                    application/json:
                        schema: GeoKodingRespons
    """
    _ = ut.deserialize_input_params(args, md.InputPunktSokGeojsonSchema())
    filtrer = ut.try_to_get_value_from_arg(args, 'filtrer')
    return_srid = ut.try_to_get_value_from_arg(args, 'utkoordsys')
    filters = ut.create_filtering_dict(filtrer)
    max_features = ut.try_to_get_value_from_arg(args, 'maksTreff')
    query = db.Queries(return_srid).eiendom_distance_teig(max_features)
    radius = args['radius']
    ost, nord = args['ost'], args['nord']
    koordsys = args['koordsys']
    search_string = ut.decode_query_string(request.query_string)
    logger.debug('Search parameters: %s' % request.args.to_dict())
    query_input = ost, nord, koordsys, radius
    output = db.DbConn().perform_query_format_response(query, query_input)
    formatted_output = ut.create_geojson_output(output, 'geojson', return_srid)
    filterModel = ut.filter_model(md.GeoKodingRespons, filters)
    return ut.return_jsonify_dump(filterModel, formatted_output, many=False)


spec = apispec_generate.spec

with app.test_request_context():
    spec.path(view=sok_eiendom)
    spec.path(view=get_eiendom_near_point)
    spec.path(view=get_eiendom_teig_near_point)


@app.route('/openapi.json')
def openapi_json():
    return jsonify(spec.to_dict())


@app.route('/')
@app.route('/index.html')
def swagger_ui():
    return render_template('swagger-ui.html')


if __name__ == '__main__':
    app.run(debug=False)  # Start a development server
