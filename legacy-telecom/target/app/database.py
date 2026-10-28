"""Données fictives du laboratoire. Aucun flag dans la base applicative."""
import sqlite3
from pathlib import Path


def initialize(path, password):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript("""
            DROP TABLE IF EXISTS offers;
            DROP TABLE IF EXISTS employees;
            CREATE TABLE offers (id INTEGER PRIMARY KEY, name TEXT, price TEXT, description TEXT);
            CREATE TABLE employees (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT);
            INSERT INTO offers VALUES
              (1, 'Ligne Essentielle', '9,90 € / mois', 'Téléphonie fixe et assistance en agence.'),
              (2, 'ADSL Découverte', '19,90 € / mois', 'Internet et téléphone pour toute la maison.'),
              (3, 'Pro Connect', '39,90 € / mois', 'Une ligne dédiée aux petites entreprises.');
        """)
        # Stockage en clair intentionnel pour ce scénario débutant.
        db.execute("INSERT INTO employees VALUES (1, 'support', ?, 'Maintenance Linux / SSH')", (password,))
