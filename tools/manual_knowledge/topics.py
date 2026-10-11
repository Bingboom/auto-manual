"""Controlled topic vocabulary for knowledge observation (Phase 2a, P2-2).

Each topic lists language-neutral anchors (units, port names, marks) and word
stems from all nine EU manual languages in one flat list. A stem from another
language almost never fires on unrelated text, and keeping the lists flat
avoids per-language tables. Stems are anchored where a bare form would collide
with another meaning: *luz solar* (sunlight) is not PV input, *descarga
eléctrica* (electric shock) is not charging, French *prendre en charge* (to
support) is not charging, and English *kind* is not German *Kind*.

Patterns match case-insensitively unless scoped ``(?-i:...)``, on NFKC text with
Unicode word boundaries. An item that matches nothing keeps ``topic: []`` and the
``topic_unknown`` review flag; nothing is guessed.
"""
from __future__ import annotations

import re
import unicodedata

_TOPICS: dict[str, tuple[str, ...]] = {
    "ups": (
        r"(?-i:\bUPS\b)", r"(?-i:\bASI\b)", r"(?-i:\bДБЖ\b)", r"\b0\s?ms\b", r"uninterruptible",
        r"unterbrechungsfrei", r"sans interruption", r"ininterrumpid", r"continuità", r"ononderbroken",
        r"bezprzerwow", r"ininterrupt", r"безперебійн",
    ),
    "energy_saving": (
        r"energy[- ]sav", r"energiespar", r"économie d.énergie", r"ahorro (?:de )?energ", r"risparmio energetico",
        r"energiebesparing", r"oszczędz\w* energii", r"economia de energia", r"poupança de energia",
        r"енергозбереж",
    ),
    "ac_output": (
        r"(?-i:\bAC\b)[- ]?(?:output|outlet|socket|port)", r"(?-i:\bAC\b)-?ausg", r"wechselstrom",
        r"(?:sortie|prise)s? (?:CA|AC)\b", r"(?:salida|toma)s? (?:de )?(?:CA|AC)\b",
        r"(?:uscit|pres)[ae] (?:CA|AC)\b", r"(?:AC|wisselstroom)-?uitgang",
        r"(?:wyjści|gniazd)\w* (?:AC|prądu przemiennego)", r"(?:saída|tomada)s? (?:CA|AC)\b", r"змінного струму",
        r"(?:вихід|розетк)\w* AC\b",
    ),
    "dc_usb_car": (
        r"(?-i:\bUSB\b)", r"\btype-c\b", r"\b12\s?[vв]\b", r"(?-i:\bDC\b)", r"(?-i:\bCC\b)",
        r"\bcar[- ](?:charg|port|outlet|socket)", r"cigarette lighter", r"zigarettenanzünder", r"\bauto-?lade",
        r"\bkfz\b", r"allume-cigare", r"chargeur (?:de |pour )?voiture", r"\bencendedor\b|\bmechero\b",
        r"(?:para|de) (?:coche|automóvil|vehículo)\b", r"(?:pour|de) voiture\b", r"accendisigari",
        r"(?:per|da) auto\b", r"sigarettenaansteker", r"\bauto-?(?:lader|oplader|laadkabel)", r"zapalniczk",
        r"samochodow", r"\bisqueiro\b", r"(?:veicular|de carro|automotivo)\b", r"прикурювач", r"автомобільн",
        r"від автомобіля", r"voor de auto\b", r"\bauto-?accu",
    ),
    "pv_input": (
        r"(?-i:\bPV\b)", r"photovolta", r"fotovolta",
        r"solar[- ]?(?:panel|modul|paneel|eingang|ladung|charg|input)", r"panel(?:es)? solar",
        r"panneaux? solaires?", r"(?:recharge|charge|entrée) solaire", r"pannell[oi] solar[ei]",
        r"(?:ricarica|ingresso) solare", r"zonnepane(?:e)?l", r"\bzonne-?(?:energie|ingang)", r"panel\w* słoneczn",
        r"ładowani\w* słoneczn", r"painel solar|painéis solares", r"(?:carregamento|entrada) solar",
        r"сонячн\w* (?:панел|заряд|вход)", r"solarsaga",
    ),
    "grounding": (
        r"\bground(?:ed|ing)\b", r"\bearth(?:ed|ing)\b", r"\bground (?:wire|terminal|cable)", r"\berdung",
        r"\bgeerdet", r"mise à la terre", r"(?:toma|conexión|puesta) a tierra", r"messa a terra", r"\baarding",
        r"\bgeaard", r"uziemi", r"aterrament|aterrad", r"заземл",
    ),
    "temperature": (
        r"°\s?[CF]\b", r"temperat", r"températ", r"температур", r"\b(?:heat|hot|overheat\w*|cold|freez\w*)\b",
        r"\bhitze", r"\bwärme", r"\bheiß", r"überhitz", r"\bkälte", r"\bfrost", r"\bchaleur", r"\bchaud",
        r"surchauffe", r"thermique", r"\bfroid", r"\bgel\b", r"\bcalor\b", r"\bcaliente", r"sobrecalent",
        r"\bfrío\b", r"\bcongel", r"\bcalore", r"\bcald[oaie]\b", r"surriscald", r"\bfredd", r"\bgelo\b",
        r"\bhitte\b", r"\bwarmte", r"\bheet\b", r"oververhit", r"\bkoude?\b", r"\bvorst\b", r"\bciepł", r"\bgorąc",
        r"przegrz", r"\bzimn", r"\bmróz|\bmroź", r"\bquente", r"superaquec", r"\bfrio\b", r"\bспек", r"\bгаряч",
        r"\bтепл", r"перегрів", r"\bхолод", r"\bмороз",
    ),
    "battery": (
        r"batter", r"\bbater[ií]", r"\bakku", r"\bpiles?\b", r"accu(?:['’]s|s)?\b", r"accumulat", r"akkumulat",
        r"acumulad", r"lithi", r"\blítio", r"\blitio", r"\bli-?ion\b", r"akumulator", r"акумулятор", r"батаре",
        r"літі",
    ),
    "app_wireless": (
        r"\bapps?\b", r"wi-?fi", r"\bwlan\b", r"bluetooth", r"wireless", r"drahtlos", r"\bsans fil\b",
        r"inalámbric", r"senza fili", r"draadloos", r"bezprzewodow", r"\bsem fio\b", r"бездротов", r"\baplikacj",
        r"\baplicativo", r"\bдодат(?:ок|ку|ка|ки)\b",
    ),
    "connection": (
        r"\b(?:dis)?connect", r"\b(?:un)?plug", r"\binsert", r"\banschl(?:ie|ü|u)ß", r"\bangeschlossen",
        r"\bverbunden", r"stecker", r"steckdose", r"\b(?:ein|aus)?steck(?:en|t)\b", r"\beingesteckt",
        r"\bschließen sie\b[^.]{0,60}\ban\b", r"\bdébranch", r"\bfiche\b", r"\binsér", r"\b(?:des)?enchuf",
        r"\binsert(?:ad|e)", r"\bspin[ae]\b", r"\binserit", r"\bstekker", r"\baangesloten", r"\bverbonden",
        r"\bverbinding", r"\bloskoppel", r"\bwtyczk", r"\bplugue", r"\binserid", r"\bвилк", r"\bвстав",
        r"\banschlu", r"\bverbind", r"\bbranch(?:er|ez|ement)\b", r"\braccord", r"\bconnexion", r"\b(?:des)?conect",
        r"\bconex(?:ión|iones|ão|ões)", r"\b(?:s)?colleg", r"\baansluit", r"\bkoppel", r"\b(?:pod|od|po)łącz",
        r"\bпід[’']?(?:ключ|єдн)", r"\bвід[’']?(?:ключ|єдн)", r"\bз[’']єдн",
    ),
    "electrical": (
        r"electric(?:al)?\s+shock", r"electrocut", r"short[- ]?circuit", r"stromschlag",
        r"elektrische[nrs]? schlag", r"kurzschl(?:uss|üss)", r"chocs? électriques?", r"électrocution",
        r"courts?-circuits?", r"descargas? eléctricas?", r"electrocución", r"cortocircuit", r"scoss[ae] elettric",
        r"folgorazione", r"elektrische schok", r"elektrocutie", r"kortsluiting", r"porażeni\w* prądem",
        r"\bzwar(?:ci|ć)", r"choques? elétricos?", r"eletrocussão", r"curtos?[- ]circuitos?",
        r"ураженн\w* електричн", r"електричн\w* (?:удар|струм)", r"коротк\w* замикан",
    ),
    "charging": (
        r"(?<!en )\bcharg(?:e|es|ed|ing|er|ers|ez|ement|eur|eurs)\b", r"\brecharg",
        r"\blade(?:n|gerät|zeit|vorgang|strom|kabel|leistung)?\b", r"\bladung\b",
        r"lade(?:kabel|gerät|zeit|vorgang|strom|leistung|anschluss)", r"\baufla(?:den|dung)", r"\baufgeladen",
        r"aufzuladen", r"\blaad(?:t)?\b", r"\b(?:op)?geladen\b", r"\bcarg(?:a|ar|ando|ue|ador|adores)\b",
        r"\brecarg", r"\bricaric", r"\bcaric(?:a|are|amento|atore)\b", r"\bopla(?:den|ad|der)", r"\blader\b",
        r"\bładow", r"\bnaładow", r"\bcarreg", r"\brecarreg", r"заряд",
    ),
    "storage_transport": (
        r"\bstor(?:e|ed|es|ing)\b", r"(?<!energy )\bstorage\b", r"lager(?:zeit|temperatur|ort|bedingung)",
        r"\btransport", r"\bship(?:ping|ped|ment)?\b", r"\baircraft", r"\bairplane", r"\bflights?\b",
        r"\blager(?:n|ung)?\b", r"\bgelager", r"\baufbewahr", r"\bstock(?:er|age|é|ez)\b", r"\bentrepos",
        r"\bconserv(?:er|ez|ation|are|azione|ato|ata|ati|ate|e|ado|ada|ar)\b", r"\balmacen", r"\bguard(?:ar|e)\b",
        r"\bstoccag", r"\bimmagazzin", r"\btrasport", r"\bopslag", r"\bopslaan", r"\bopgeslagen", r"\bopberg",
        r"\bbewa(?:ren|ar)\b", r"\bprzechow", r"\barmazen", r"\bзберіг", r"\bтранспорт", r"\bперев(?:е|о)з",
    ),
    "disposal": (
        r"\bdisposal\b", r"\bdispos(?:e|ed|ing) of\b", r"recycl", r"\bwaste\b", r"\bentsorg", r"hausmüll",
        r"\babfall", r"\bélimin", r"\bdéchet", r"ordures ménagères", r"\bdesech", r"\brecicl", r"\bresiduos?\b",
        r"\bbasura", r"\bsmalt", r"\bricicl", r"\brifiut", r"\bafval", r"\bafvoer", r"\bafgevoerd", r"\butyliz",
        r"\bodpad", r"\brecykl", r"\bdescart", r"\bresíduos?\b", r"\blixo\b", r"утиліз", r"відход", r"переробк",
        r"сміття",
    ),
    "children": (
        r"\bchild(?:ren)?\b", r"\bkids?\b", r"\binfants?\b", r"(?-i:\bKind\b)", r"\bkinder(?:n|en)?\b",
        r"\benfants?\b", r"\bniñ[oa]s?\b", r"\bbambin[oi]\b", r"\bdzie(?:ci|cko|ciom|ćmi|cka|cku)\b",
        r"\bcrianças?\b", r"\bдіт(?:и|ей|ям|ьми)\b", r"\bдитин",
    ),
    "fire": (
        r"\bfires?\b", r"\bflames?\b", r"\bflammable", r"\bexplo", r"\bburn", r"\bfeuer",
        r"\bbrand(?:gefahr|gevaar)?\b", r"\bflamm", r"\bentzünd", r"\bfeu\b", r"\bincendi", r"\binflamma",
        r"\bfuego\b", r"\bllamas?\b", r"\binflamab", r"\bfuoco\b", r"\bfiamm", r"\binfiammab", r"\besplo",
        r"\bvuur\b", r"\bvlam", r"\bontvlam", r"\bogie[ńn]", r"\bogni[aeu]?\b", r"\bpożar", r"\bpłomie",
        r"\bwybuch", r"łatwopal", r"\bfogo\b", r"\bincêndio", r"\bchamas?\b", r"\binflamáve", r"\bвогн", r"\bвогон",
        r"\bпожеж", r"\bполум", r"\bвибух", r"займист",
    ),
    "water": (
        r"\bwater\b", r"\bmoist", r"\bliquids?\b", r"\brain\b", r"\bwet\b", r"\bhumid", r"\bwasser", r"\bfeucht",
        r"\bflüssig", r"\bregen\b", r"\bnass", r"\beau\b", r"\bliquide", r"\bpluie", r"\bmouill", r"\bagua\b",
        r"\bhúmed", r"\bhumedad", r"\blíquid", r"\blluvia", r"\bmojad", r"\bacqua\b", r"\bumid", r"\bliquid",
        r"\bpioggia", r"\bbagnat", r"\bvocht", r"\bvloeistof", r"\bnat\b", r"\bwod(?:a|y|ą|zie|ę)\b", r"\bwilgo",
        r"\bciecz", r"\bdeszcz", r"\bmokr", r"\bágua\b", r"\bchuva", r"\bmolhad", r"\bвод(?:а|и|ою|у|і)\b",
        r"\bволог", r"\bрідин", r"\bдощ", r"\bмокр",
    ),
    "disassembly": (
        r"\bdisassembl", r"\bdismantl", r"\brepair", r"\bzerleg", r"\bdemont", r"\bauseinander", r"\breparier",
        r"\bdémont", r"\brépar", r"\bdesmont", r"\bdesarm", r"\brepar", r"\bsmont", r"\bripar", r"\buit elkaar",
        r"\brozmontow", r"\brozbier", r"\bnapraw", r"\bрозбир", r"\bремонт",
    ),
}
TOPICS = tuple(_TOPICS)
_PATTERNS = {topic: re.compile("|".join(stems), re.IGNORECASE) for topic, stems in _TOPICS.items()}


def classify(text: str) -> list[str]:
    """Every controlled topic whose anchors or stems occur in ``text``, in vocabulary order."""
    normalized = unicodedata.normalize("NFKC", text)
    return [topic for topic, pattern in _PATTERNS.items() if pattern.search(normalized)]
