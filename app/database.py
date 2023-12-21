#!/usr/bin/env python3

import logging

from flask import abort
import psycopg2

import config as cf

logger = logging.getLogger(__name__)


class DbConn():
    """Connect to the db, perform a query and format the response"""

    def __init__(self):
        logger.info('Initializing database connection.')
        try:
            self.conn = psycopg2.connect(
                dsn=cf.db_uri, user=cf.db_user, password=cf.db_password)
            self.cur = self.conn.cursor()
        except psycopg2.errors.TooManyConnections:
            abort(500, "Databasen opplever for mange tilkoblinger, vennligst vent litt.")
        except Exception as e:
            logger.error(
                "Exception under databaseconnection: {}".format(e.message))
            abort(500, "Noe gikk galt, prøv igjen senere")

    def perform_query_format_response(self, query, userInput=False):
        queryResult = self._execute_query(query, userInput)
        return self._format_response(queryResult)

    def _execute_query(self, query, userInput=False):
        """userInput is included here because of protection against sql-injection when
        the parameters are inserted as a tuple in the cur.execute-command.
        """
        logger.debug('Query to execute: %s. With input: %s' %
                     (query, userInput))
        logger.info(f'Executing query')
        if not isinstance(userInput, tuple):
            userInput = (userInput,)
        try:
            if userInput:
                self.cur.execute(query, userInput)
            else:
                self.cur.execute(query)
        except Exception as e:
            logger.error(
                f'Encountered exception when performing query with input: "{userInput}" : {e}')
            if "srid" in str(e).lower():
                abort(400, "Koordinatsystemet/SRID er ikke støttet.")
            else:
                abort(500, 'Ukjent feil oppstod.')
        result = self.cur.fetchall()
        self.conn.commit()
        logger.info(f'Executed query')
        logger.debug('Query result: %s' % result)
        return result

    def _format_response(self, query_result):
        outList = []
        if len(query_result) == 0:
            logger.debug('Ingen treff.')
            return outList
        for row in query_result:
            tempDict = {}
            for index, data in enumerate(row):
                colName = self.cur.description[index][0]
                tempDict[colName] = data
            outList.append(tempDict)
        logger.info(f'Formatted query result, first element: {outList[0]}')
        return outList

    def __del__(self):
        """close connection if not already done"""
        try:
            self.conn.close()
        except AttributeError:
            return


class Queries:

    def __init__(self, return_srid):
        self.return_srid = return_srid
        if self.return_srid != cf.db_srid:
            self.rep_point = """
            json_build_object(
                'representasjonspunkt_ost',
                    round(st_x(st_transform(representasjonspunkt, {0}))::numeric, 5),
                'representasjonspunkt_nord',
                    round(st_y(st_transform(representasjonspunkt, {0}))::numeric, 5),
                'koordsys',
                    {0}
            ) AS representasjonspunkt_json
            """.format(self.return_srid)
        else:
            self.rep_point = """representasjonspunkt_json"""


    def readiness():
        return 'SELECT 1;'
    
    def eiendom_sok(self, teig=False, where=''):
        if teig:
            geom = 'ST_Asgeojson(ST_Transform(omrade_4258_curve_to_line, {0}), 7, 0)::json as rep_geojson,'.format(
                self.return_srid)
        else:
            geom = 'ST_Asgeojson(ST_Transform(representasjonspunkt, {0}), 5, 0)::json as rep_geojson,'.format(
                self.return_srid)
        return """
                    SELECT
                        objtype,
                        count(*) OVER() AS result_count,
                        gardsnummer,
                        bruksnummer,
                        festenummer,
                        seksjonsnummer,
                        kommunenummer,
                        hoved,
                        lokalid,
                        {1}
                        oppdateringsdato,
                        matrikkelnummertekst,
                        teigmedflerematrikkelenheter,
                        uregistrertjordsameie,
                        noyaktighetsklasseteig
                      FROM api_teig_anlegg {0}
                    ;""".format(where, geom)

    def eiendom_distance(self, pagination=''):
        return """WITH input_geom AS (
                    SELECT ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), 25833) AS geom
                    )
                SELECT
                    objtype,
                    count(*) OVER() AS result_count,
                    gardsnummer,
                    bruksnummer,
                    festenummer,
                    seksjonsnummer,
                    hoved,
                    kommunenummer,
                    lokalid,
                    {0},
                    representasjonspunkt_geojson,
                    oppdateringsdato,
                    matrikkelnummertekst,
                    teigmedflerematrikkelenheter,
                    uregistrertjordsameie,
                    noyaktighetsklasseteig,
                    ST_Distance(ig.geom, omrade_25833) AS distanse
                FROM api_teig_anlegg, input_geom ig
                WHERE ST_DWithin(ig.geom, omrade_25833, %s)
                ORDER BY distanse, hoved
                {1};""".format(self.rep_point, pagination)

    def eiendom_distance_teig(self, max_features):
        return """WITH input_geom AS (
                    SELECT ST_Transform(ST_GeomFromText('POINT(%s %s)', %s), 25833) AS geom
                    )
                SELECT
                    objtype,
                    gardsnummer,
                    bruksnummer,
                    festenummer,
                    seksjonsnummer,
                    hoved,
                    kommunenummer,
                    lokalid,
                    ST_Asgeojson(ST_Transform(omrade_4258_curve_to_line, {0}), 7, 0)::json as geojson,
                    oppdateringsdato,
                    matrikkelnummertekst,
                    teigmedflerematrikkelenheter,
                    uregistrertjordsameie,
                    noyaktighetsklasseteig,
                    ST_Distance(ig.geom, omrade_25833) AS distanse
                FROM api_teig_anlegg, input_geom ig
                WHERE ST_DWithin(ig.geom, omrade_25833, %s)
                ORDER BY distanse, hoved
                LIMIT {1};""".format(self.return_srid, max_features)
