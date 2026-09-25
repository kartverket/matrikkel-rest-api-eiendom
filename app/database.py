#!/usr/bin/env python3

import logging
import signal
import sys
from flask import abort
import psycopg2
from psycopg2.pool import ThreadedConnectionPool as _ThreadedConnectionPool
from threading import Semaphore
import config as cf

logger = logging.getLogger(__name__)

# ThreadedConnectionPool doesn't have any blocking functionality for getconn(), when maxconn is exceeded 
# https://stackoverflow.com/questions/48532301/python-postgres-psycopg2-threadedconnectionpool-exhausted/49366850#49366850
# Also adding signal handling if Kubernetes kills a container
class ThreadedConnectionPool(_ThreadedConnectionPool):
    def __init__(self, minconn, maxconn, *args, **kwargs):
        self._semaphore = Semaphore(maxconn)
        super().__init__(minconn, maxconn, *args, **kwargs)
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def getconn(self, *args, **kwargs):
        self._semaphore.acquire()
        try:
            return super().getconn(*args, **kwargs)
        except:
            self._semaphore.release()
            raise
    
    def handle_signal(self, sig, frame):
        exit_status = 0
        logger.info("Recieved signal: {}. Closing all db-connection(s)".format(signal.Signals(sig).name))

        try:
            self.closeall()
        except Exception as e:
            logger.error(e)
            exit_status = 1
        sys.exit(exit_status)

    def putconn(self, *args, **kwargs):
        try:
            super().putconn(*args, **kwargs)
        finally:
            self._semaphore.release()

    def closeall(self):
        return super().closeall()


class DbConn():
    """Connect to the db, perform a query and format the response"""

    pool = ThreadedConnectionPool(
                minconn=cf.min_db_connections, maxconn=cf.max_db_connections,
                dsn=cf.db_uri, user=cf.db_user, password=cf.db_password
            )
    
    def get_db_connection(self):
        try:
            return self.pool.getconn()
        except Exception as e:
            logger.error(
                "Exception under databaseconnection: {}".format(e))
            abort(500, "Noe gikk galt, prøv igjen senere")  

    def abort_with_db_release(self, db_connection, status_code, message=None):
        if db_connection is not None:
            self.pool.putconn(db_connection)
        abort(status_code, message)

    def perform_query_format_response(self, query, userInput=False):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        queryResult = self._execute_query(cursor, connection, query, userInput)
        formatted_response = self._format_response(cursor, queryResult)
        self.pool.putconn(connection)
        return formatted_response

    def _execute_query(self, cursor, connection, query, userInput=False):
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
                cursor.execute(query, userInput)
            else:
                cursor.execute(query)
        except Exception as e:
            logger.error(
                f'Encountered exception when performing query with input: "{userInput}" : {e}')
            if "srid" in str(e).lower():
                self.abort_with_db_release(connection, 400, "Koordinatsystemet/SRID er ikke støttet.")
            else:
                self.abort_with_db_release(connection, 500, 'Ukjent feil oppstod.')
        result = cursor.fetchall()
        connection.commit()
        logger.info(f'Executed query')
        logger.debug('Query result: %s' % result)
        return result

    def _format_response(self, cursor, query_result):
        outList = []
        if len(query_result) == 0:
            logger.debug('Ingen treff.')
            return outList
        for row in query_result:
            tempDict = {}
            for index, data in enumerate(row):
                colName = cursor.description[index][0]
                tempDict[colName] = data
            outList.append(tempDict)
        logger.info(f'Formatted query result, first element: {outList[0]}')
        return outList


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
