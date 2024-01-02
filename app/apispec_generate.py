"""
Generates an open-api spec from the endpoints and models. Remember to activate the
virtualenv.
"""
from apispec import APISpec
from apispec_webframeworks.flask import FlaskPlugin
from apispec.ext.marshmallow import MarshmallowPlugin
import config as cf

scheme = "http" if cf.is_dev else "https"

spec = APISpec(
    title='Åpent eiendoms-API for lokalisering',
    version='1.1.0',
    openapi_version='3.0.3',
    info=dict(
        description="""
API fra Kartverket for geokoding eller lokalisering av eiendommer. Finn eiendommer ved en posisjon, eller finn posisjonen til et matrikkelnummer.

I dette APIet er eiendommer definert som matrikkelenheter med avgrensing i kartet. Datagrunnlaget har vanligvis et døgn forsinkelse fra Matrikkelen.

Obs. Eiendomskartet i matrikkelen kan være ufullstendig eller upresist.

Det er ikke nødvendig med innlogging/autorisasjon for å bruke APIet.

Medio desember 2023 ble APIet flyttet til et nytt endepunkt som er tilgjengelig på <a href="https://api.kartverket.no/eiendom/v1">https://api.kartverket.no/eiendom/v1</a>.
Det tidligere endepunktet <a href="https://ws.geonorge.no/eiendom/v1">https://ws.geonorge.no/eiendom/v1</a> vil være tilgjengelig inntil videre, og vil fungere som en proxy til det nye endepunktet.
Vi anbefaler likevel å bytte til det nye endepunktet.

Større eller ikke-kompatible endringer i APIet vil bli annonsert med minst 3 måneder forvarsel på <a href="https://status.kartverket.no">https://status.kartverket.no</a>.

Område for eiendom kan leveres, men type grense eller kvalitetsinformasjon om grenser leveres IKKE i dette APIet.
Hvis man ønsker å hente ned datagrunnlaget så anbefales det å laste ned filene som er tilgjengeliggjort via <a href="https://www.geonorge.no">geonorge.no</a> (Matrikkelen-Eiendomskart Teig).
For direkte henting av grenseinformasjon fra Matrikkelen, - bruk MatrikkelAPI."""),
    servers=[
        dict(
            url=scheme+"://"+cf.app_ingress+cf.basepath
        )
    ],
    plugins=[
        FlaskPlugin(),
        MarshmallowPlugin(),
    ]
)
