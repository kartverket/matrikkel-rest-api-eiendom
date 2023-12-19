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
<p>Det er ikke nødvendig med innlogging/autorisasjon for å bruke APIet. Større funksjonalitetsødeleggende endringer i API-et vil bli annonsert minst 3 måneder i forveien på <a href="https://geonorge.no/aktuelt/varsler/Tjenestevarsler/">Geonorge Tjenestevarsler</a></p>
<p>I dette API-et er eiendommer definert som matrikkelenheter med avgrensing i kartet. Datagrunnlaget har vanligvis et døgn forsinkelse fra Matrikkelen.
Obs. Eiendomskartet i matrikkelen kan være ufullstendig eller upresist.</p>
<p>Område for eiendom kan leveres, men type grense eller kvalitetsinformasjon om grenser leveres IKKE i dette API-et. Hvis man ønsker å hente ned datagrunnlaget så anbefales det å laste ned filene som er tilgjengeliggjort via <a href="https://www.geonorge.no">geonorge.no</a> (Matrikkelen-Eiendomskart Teig). For direkte henting av grenseinformasjon fra Matrikkelen, - bruk MatrikkelAPI.</p>
        """),
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
