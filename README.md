# Eiendoms API

API fra Kartverket for geokoding eller lokalisering av eiendommer. Finn eiendommer ved en posisjon, eller finn posisjonen til et matrikkelnummer.
I dette APIet er eiendommer definert som matrikkelenheter med avgrensing i kartet. Datagrunnlaget har vanligvis et døgn forsinkelse fra Matrikkelen.

## Deployment etc

- Bygg og deploy skjer vha. build-push-deploy og promote-test-prod workflows.

# Testing
For å teste lokalt:
Etter at du har aktivert venv:
1. installer tavern via dev-requirements.txt-filen:
2. pip install -r dev_requirements.txt --upgrade
3. Eksporter url-en til dev-serveren, f.eks.: `export TAVERN_TEST_URL='http://localhost:5000'`
4. Naviger til integration_tests-mappen og kjør: `tavern-ci test_api.tavern.yaml --tavern-global-cfg=tavern_external_config.yaml`

# Spørsmål og svar:

## Besvarte:
- hvilken lokalid skal benyttes?
    - Hent lokalid for teig og for anleggsprojeksjonsflate
- Hvilken fellesbetegnelse skal vi gi hovedflate/hovedteig?
    - Kall hovedteig/hovedflate for hovedområde, eventuelt hovedareal
- Sortering?
    - Hovedareal først. Man skal kun kunne få treff på en eiendom.
- Hvordan håndtere "falske" matrikkelnummer, altså når matrikkelnummer er 0/1 eller 0/0?
    - sett de inviduelle nummerne i responsen til "null". Så hvis gardsnummer er 0 så sett alt unntatt kommunenummer til "null"
- kommunenavn - ikke i datasettet, og det finnes kommuner som deler navn. Ikke unik id.
    - Venter med kommunenavn
- Hva skal punktsøk returnere?
    - punktsøk: treffer teig med flere matrikkelenheter: list opp alle individuelt


## Ubesvarte:
- Hva skal vi gjøre når vi får treff på eiendom som er fullstendig seksjonert bort?
    - Alt 1: velge ut en seksjon på måfå.
    - Alt 2: Ikke returnere noenting (eiendommen har jo i realiteten ikke noe representasjonspunkt).
    - Alt 3: returnere alt som ligger "under" eiendommen (tror dette er mest brukervennlig)

