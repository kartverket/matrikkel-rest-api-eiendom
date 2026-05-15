#!/usr/bin/env python3
from collections import OrderedDict

from marshmallow import Schema, fields, validate
from marshmallow.validate import Range

import config as cf


# Standard models


class GeoJsonCoords(Schema):
    type = fields.Str()
    coordinates = fields.List(fields.Raw())


class GeoJsonGeometry(Schema):
    geometry = fields.Nested(GeoJsonCoords)


class GeojsonEpsg(Schema):
    name = fields.Str()


class GeojsonCrs(Schema):
    type = fields.Str()
    properties = fields.Nested(GeojsonEpsg)


class GeojsonStandard(Schema):
    type = fields.Str()


class Geojson(GeojsonStandard):
    coordinates = fields.List(fields.Float())


class GeojsonPoly(GeojsonStandard):
    coordinates = fields.List(fields.List(fields.List(fields.Float())))


class GeoJsonCoordinates(GeojsonStandard):
    coordinates = fields.List(fields.Raw())
    type = fields.Str()


class GeojsonFeature(Schema):
    type = fields.Str()
    properties = fields.Raw()
    geometry = fields.Nested(GeoJsonCoordinates)


class GeojsonFeatureCollection(Schema):
    type = fields.Str()
    features = fields.Nested(GeojsonFeature, many=True)
    crs = fields.Nested(GeojsonCrs)


class Fylker(Schema):
    fylkesnavn = fields.String()
    fylkesnummer = fields.String()


class Kommuner(Schema):
    kommunenavn = fields.String()
    kommunenummer = fields.String()


class Representasjonspunkt(Schema):
    dict_class = OrderedDict

    øst = fields.Float(metadata={'description': ''}, attribute='representasjonspunkt_ost')
    nord = fields.Float(metadata={'description': ''}, attribute='representasjonspunkt_nord')
    koordsys = fields.Int(
        dump_default=cf.db_srid,
        metadata={'description': 'Koordinatsystemet til representasjonspunktet, oppgis som en SRID (altså tall-delen av en EPSG-kode, f.eks. 4258 eller 25833).'})


class MatrikkelnummerDeler(Schema):
    dict_class = OrderedDict

    kommunenummer = fields.String(
        metadata={'description': 'Kommunenummer bestående av fire tegn med ledende 0 om nødvendig.'},
        validate=[validate.Length(min=4, max=4), validate.Regexp(r"""^[0123456789]*$""")])
    gardsnummer = fields.Integer(metadata={'description': 'Del av et matrikkelnummer'})
    bruksnummer = fields.Integer(metadata={'description': 'Del av et matrikkelnummer'})
    festenummer = fields.Integer(metadata={'description': 'Del av et matrikkelnummer'})
    seksjonsnummer = fields.Integer(metadata={'description': 'Del av et matrikkelnummer'})


# Input


class InputTeigOrRepresentasjonspunkt(Schema):
    omrade = fields.Boolean(
        metadata={'description': 'Angi som "true" for å hente ut område i stedet for kun representasjonspunktet.  Område er flater avgrenset av linjer som kan være eiendomsgrenser (av ulik kvalitet), men også hjelpelinjer der grenser mangler i matrikkelen.  For volumer over eller under bakken er område et «fotavtrykk».'},
        dump_default=False,
        load_default=False)


class InputMetadata(Schema):
    treffPerSide = fields.Integer(
        metadata={'description': 'Antall treff per side. Minimum 1, maksimum 500.'},
        validate=validate.Range(min=1, max=500),
        load_default=10)
    side = fields.Integer(
        metadata={'description': 'Sidenummeret som skal vises i returen. Minimum 1, maksimum 500.'},
        validate=validate.Range(min=1, max=500),
        load_default=1)


class InputReturnSrid(Schema):
    utkoordsys = fields.Integer(
        metadata={'description': f'Angi det koordinatsystemet som du ønsker at geometrien i returen skal transformeres til, oppgis som en SRID (altså tallene i en EPSG-kode, f.eks. 4258 eller 25833). Standard er {cf.db_srid}. 4258 er i praksis identisk med 4326. Hvis det bes om et annet koordinatsystem enn det som er standard for geojson (4326/4258) så inkluderes et CRS-element i en geojson-respons.'},
        validate=validate.Range(min=0, max=99999),
        load_default=cf.db_srid)


class InputFiltrer(Schema):
    filtrer = fields.Str(
        metadata={'description': 'Vis kun de elementene du vil ha i returen. Kommaseparert liste med nøkler. For å hente ut underobjekter bruk "."-notasjon, f.eks. &filtrer=metadata.side'})


class MatrikkelNummerSchema(Schema):
    matrikkelnummer = fields.String(
        metadata={'description': "Den offisielle benevnelsen for en eiendom. Fullstendig matrikkelnummer består av kommunenummer, gardsnummer, bruksnummer, eventuelt festenummer, eventuelt seksjonsnummer, f.eks 3413-325/2 (grunneiendom), 3413-325/2/1 (festegrunn) eller 3413-6/501/0/2 (seksjon)"})


class InputEiendom(MatrikkelnummerDeler, InputTeigOrRepresentasjonspunkt, MatrikkelNummerSchema):
    dict_class = OrderedDict


class InputEiendomSchema(InputFiltrer, InputReturnSrid, InputEiendom):
    pass


class InputPunktSok(Schema):
    dict_class = OrderedDict

    ost = fields.Float(required=True, metadata={'description': "Øst-koordinaten/Longitude"})
    nord = fields.Float(required=True, metadata={'description': "Nord-koordinaten/Latitude"})
    koordsys = fields.Integer(
        required=True,
        metadata={'description': "Koordinatsystemet (EPSG) til koordinatene du søker med. Angis som en SRID, for eksempel 4258 eller 25833."},
        validate=Range(min=1, max=999999))
    radius = fields.Integer(
        required=False,
        load_default=100,
        validate=validate.Range(min=1, max=3000),
        metadata={'description': "Radius i antall meter som søket leter etter eiendommer i. Maksimum er 3000m."})


class InputPunktSokSchema(InputMetadata, InputFiltrer, InputReturnSrid, InputPunktSok):
    pass


class InputPunktSokGeojsonSchema(InputFiltrer, InputReturnSrid, InputPunktSok):
    maksTreff = fields.Integer(
        required=False,
        load_default=50,
        validate=validate.Range(min=1, max=500),
        metadata={'description': 'Maks antall objekter i GeoJSON-featurecollection responsen. Maksimum er 500.'})


# Output


class ReturDeltSchema(MatrikkelnummerDeler):
    dict_class = OrderedDict
    matrikkelnummertekst = fields.String(
        metadata={'description': 'Generert tekst ut fra hvilken matrikkelenhet teigen tilhører. Eventuelt flere matrikkelnummere skyldes manglende, uavklarte grenser eller uregistrert jordsameie.'})
    objekttype = fields.String(
        metadata={'description': 'Stedfesting/geometri hentes fra to objekttyper, teig eller anleggsprojeksjonsflate. Den siste er «fotavtrykk» av volumer som fins over eller under teiger på terrenget'},
        attribute='objtype')
    hovedområde = fields.Boolean(
        metadata={'description': 'Angir om området er teigens eller anleggsprojeksjonens hovedteig/hovedflate.'},
        attribute='hoved')
    lokalid = fields.Integer(
        metadata={'description': 'Lokal identifikator, tildelt av dataleverandør/dataforvalter (her matrikkelsystemet, Kartverket).'})
    oppdateringsdato = fields.DateTime(
        metadata={'description': 'dato for siste endring på data-objektet i matrikkelsystemet'},
        format='%Y-%m-%dT%H:%M:%M')
    teigmedflerematrikkelenheter = fields.Boolean(
        metadata={'description': 'Teigen mangler indre avgrensing mellom de registrerte matrikkelnummerene'})
    uregistrertjordsameie = fields.Boolean(
        metadata={'description': 'De registrerte matrikkelnummerene har andel i teigen'})
    nøyaktighetsklasseteig = fields.String(
        metadata={'description': 'Grov klassifisering (trafikklys) av stedfestingsnøyaktighet. (Grønt = ok, gult = sjekk!, rødt = store mangler)'},
        attribute='noyaktighetsklasseteig')


class PunktDistanse(Schema):
    meterFraPunkt = fields.Int(
        metadata={'description': "Distanse i meter til punktet det ble søkt etter."},
        attribute='distanse')


class GeokodingPropertiesSchema(ReturDeltSchema, PunktDistanse):
    dict_class = OrderedDict


class PunktSchema(ReturDeltSchema, PunktDistanse):
    representasjonspunkt = fields.Nested(
        Representasjonspunkt,
        metadata={'description': 'Punktet ligger innenfor teigens eller flatens avgrensing.'},
        attribute='representasjonspunkt_json')


class MetadataSchema(InputMetadata):
    totaltAntallTreff = fields.Integer(
        metadata={'description': 'Antall treff som søket returnerte.'})
    viserFra = fields.Integer(
        metadata={'description': 'Viser treff fra objekt nummer X i responsen.'})
    viserTil = fields.Integer(
        metadata={'description': 'Viser treff til objekt nummer X i responsen.'})
    sokeStreng = fields.String(
        metadata={'description': 'Søkestrengen som ble sendt inn til API-et.'})


class ReturMetadata(Schema):
    dict_class = OrderedDict
    metadata = fields.Nested(MetadataSchema)


class GeoJsonType(Schema):
    type = fields.Str()


class GeoJsonGeom(Schema):
    geometry = fields.Nested(GeoJsonCoordinates)


class GeokodingGeoJson(GeoJsonType, GeoJsonGeom):
    properties = fields.Nested(GeokodingPropertiesSchema)


class GeoKodingRespons(Schema):
    type = fields.Str()
    features = fields.Nested(GeokodingGeoJson, many=True)
    crs = fields.Nested(GeojsonCrs)


class PunktRespons(ReturMetadata):
    dict_class = OrderedDict
    eiendom = fields.Nested(PunktSchema, many=True)