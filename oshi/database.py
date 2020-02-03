"""
Database abstraction
"""
import json
import re
import gzip
from typing import Iterable
from os import path
from lxml import etree

CURRENT_DIRECTORY = path.dirname(__file__)
DATABASE_FILENAME = path.join(CURRENT_DIRECTORY, 'oshi_database.json')

class Database:
    """
    Represents a database connection
    """
    def __init__(self, entries):
        self.entries = entries
    def search(self, term) -> Iterable:
        """
        Returns entries that contain the term in its writings
        """
        for entry in self.entries:
            if any(term in writing for writing in entry["writings"]):
                yield entry


def connect(filename=DATABASE_FILENAME):
    """
    Loads database and returns a Database object
    """
    if not path.exists(filename):
        raise FileNotFoundError("Database file not found: " + filename)
    with open(filename, 'r') as f:
        return Database(json.load(f))

def build(filename="JMdict_e.gz", output_filename=DATABASE_FILENAME):
    """
    Builds database from a JMdict gzip or xml file and writes to database
    into output_filename
    Should be used from a command-line
    """
    extension = path.splitext(filename)[1].lower()
    if extension == ".gz":
        with gzip.open(filename) as f:
            tree = etree.parse(f)
    elif extension == ".xml":
        tree = etree.parse(filename)
    else:
        raise ValueError("File extension not supported: " + extension)

    entries = []
    # variables starting with x contain xml element(s)
    for xentry in tree.getroot():
        entry = {}
        entry["writings"] = [x.find('keb').text for x in xentry.findall('k_ele')]
        entry["readings"] = [x.find('reb').text for x in xentry.findall('r_ele')]
        xsenses = xentry.findall('sense')
        senses = []
        for xsense in xsenses:
            tags = []
            for xtag in xsense.findall('pos') + xsense.findall('misc'):
                for match in re.search(r'&(.*?);', xtag.text) or []:
                    tags.append(match)
            glosses = [x.text for x in xsense.findall('gloss')]
            senses.append({"glosses": glosses, "tags": tags})
        entry["senses"] = senses
        entries.append(entry)
    with open(output_filename, 'w') as f:
        json.dump(entries, f)
