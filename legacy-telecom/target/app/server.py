"""Portail volontairement vulnérable, réservé au laboratoire local."""
import html
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

STATIC = Path(__file__).parent / 'static'


def page(title, body, legacy=False):
    return f'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Legacy Telecom</title><link rel="stylesheet" href="/static/style.css"></head>
<body><header><a class="brand" href="/">legacy<span>telecom</span><b>LT</b></a>
<nav><a href="/">Accueil</a><a href="/offres">Nos offres</a><a href="/assistance">Assistance</a></nav></header>
<main>{body}</main><footer>Legacy Telecom · {'Portail historique — catalogue 2015' if legacy else 'Vos connexions, notre métier.'}
<span>Entreprise fictive · environnement d’entraînement local</span></footer></body></html>'''


class Handler(BaseHTTPRequestHandler):
    server_version = 'LegacyPortal/1.4'
    sys_version = ''

    def send(self, status, body, content_type='text/html; charset=utf-8'):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == '/healthz':
            self.send(200, 'ok', 'text/plain')
        elif url.path == '/static/style.css':
            self.send(200, (STATIC / 'style.css').read_text(), 'text/css; charset=utf-8')
        elif url.path == '/robots.txt':
            self.send(200, 'User-agent: *\nDisallow: /legacy/\n', 'text/plain')
        elif url.path == '/':
            self.send(200, page('Bienvenue', '''<section class="hero"><div><p class="eyebrow">DEPUIS 1998 · PROCHE DE VOUS</p>
<h1>Le lien qui<br>nous rapproche.</h1><p class="lead">Internet, téléphone et conseils : une connexion simple,<br>pour les moments qui comptent.</p>
<a class="button" href="/offres">Découvrir nos offres <span>↗</span></a></div><div class="illustration" aria-hidden="true"><div class="orbit"></div><div class="orbit second"></div><div class="router">LT<span>● ● ●</span></div><p>TOUJOURS CONNECTÉS.</p></div></section>
<section class="cards"><article><span>01 / INTERNET</span><h2>Votre quotidien, connecté.</h2><p>Une offre adaptée à chaque foyer.</p></article>
<article><span>02 / PROXIMITÉ</span><h2>Une équipe à vos côtés.</h2><p>Des interlocuteurs qui vous connaissent.</p></article>
<article><span>03 / CONTINUITÉ</span><h2>Déjà client ?</h2><p>La migration de votre espace est en cours. Les anciennes références restent consultables au catalogue historique.</p></article></section>'''))
        elif url.path == '/offres':
            self.send(200, page('Nos offres', '''<p class="eyebrow">RESTONS CONNECTÉS</p><h1>Une offre pour chacun.</h1>
<p class="lead">Notre nouvel espace commercial arrive bientôt.</p><a class="button" href="/legacy/">Consulter le catalogue historique ↗</a>'''))
        elif url.path == '/assistance':
            self.send(200, page('Assistance', '''<p class="eyebrow">UNE QUESTION ?</p><h1>Nous sommes là.</h1>
<p class="lead">Retrouvez les références de votre abonnement dans notre catalogue historique.</p>
<p>Note interne : la maintenance des archives est confiée à l’équipe support sur le serveur Linux.</p>'''))
        elif url.path in ('/legacy', '/legacy/'):
            self.send(200, page('Catalogue historique', '''<p class="eyebrow">ESPACE HISTORIQUE / 2015</p><h1>Votre ancienne offre.</h1>
<p class="lead">Sélectionnez une référence pour consulter sa fiche.</p><div class="cards">
<article><h2>Ligne Essentielle</h2><a href="/legacy/offer?id=1">Référence 1 →</a></article>
<article><h2>ADSL Découverte</h2><a href="/legacy/offer?id=2">Référence 2 →</a></article>
<article><h2>Pro Connect</h2><a href="/legacy/offer?id=3">Référence 3 →</a></article></div>''', True))
        elif url.path == '/legacy/offer':
            self.offer(parse_qs(url.query, keep_blank_values=True).get('id', ['1'])[0])
        else:
            self.send(404, page('Page introuvable', '<h1>Cette page a déménagé.</h1><a href="/">Retour à l’accueil →</a>'))

    def offer(self, offer_id):
        if len(offer_id) > 2000:
            self.send(400, page('Requête trop longue', '<h1>Requête trop longue.</h1>'))
            return
        # INTENTIONNEL : concaténation SQL exploitable dans le périmètre du labo.
        query = 'SELECT id, name, price, description FROM offers WHERE id = ' + offer_id
        db_path = Path(self.server.database).resolve().as_uri() + '?mode=ro'
        try:
            with sqlite3.connect(db_path, uri=True) as db:
                rows = db.execute(query).fetchmany(50)
        except sqlite3.Error as error:
            self.send(500, page('Erreur du catalogue', f'<p class="eyebrow">DIAGNOSTIC HISTORIQUE</p><h1>Erreur SQL</h1><pre>{html.escape(str(error))}</pre><pre>{html.escape(query)}</pre>', True))
            return
        cards = ''.join(f'<article><span>RÉFÉRENCE {html.escape(str(row[0]))}</span><h2>{html.escape(str(row[1]))}</h2><p class="price">{html.escape(str(row[2]))}</p><p>{html.escape(str(row[3]))}</p></article>' for row in rows)
        self.send(200, page('Fiche offre', '<a href="/legacy/">← Catalogue historique</a><h1>Détail des références.</h1><section class="cards">' + (cards or '<p>Aucune offre trouvée.</p>') + '</section>', True))


def create_server(host='0.0.0.0', port=8080, database='/var/lib/legacy-app/portal.db'):
    server = ThreadingHTTPServer((host, port), Handler)
    server.daemon_threads = True
    server.database = database
    return server


if __name__ == '__main__':
    # Le backend n'est accessible que par Nginx depuis la boucle locale.
    create_server(host='127.0.0.1').serve_forever()
