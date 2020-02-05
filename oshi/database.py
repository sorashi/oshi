import json
import re
import gzip
import copy
from fnmatch import fnmatch
from typing import Iterable
from os import path
from lxml import etree

CURRENT_DIRECTORY = path.dirname(__file__)
DATABASE_FILENAME = path.join(CURRENT_DIRECTORY, 'oshi_database.json')

class Database:
    """
    Represents a database connection
    Database entry structure:
        writings: List[str]
        readings: List[str]
        senses: List, each sense:
            glosses: List[str]
            tags: List[str]
    """
    def __init__(self, entries):
        self.entries = entries
    def search(self, term) -> Iterable:
        """
        Returns entries that contain the term in its writings
        """
        for entry in self.entries:
            if any(term in writing for writing in entry["writings"]):
                yield copy.deepcopy(entry)
    def find_exact(self, expression, tag_glob="*"):
        """
        Finds and returns the first entry exactly matching expression and returns
        a copy of the entry with only those senses have a tag match for tag_glob
        Returns None if no entry was found
        """
        for entry in self.entries:
            if any(expression == writing for writing in entry["writings"]):
                entry_copy = copy.deepcopy(entry)
                entry_copy["senses"] = list(
                    filter(lambda sense: any(fnmatch(x, tag_glob)
                           for x in sense["tags"]),
                           entry_copy["senses"]))
                return entry_copy
        return None

def entry_tostring(entry):
    result = ""
    result += " ".join(entry["writings"]) + "\n"
    result += " ".join(entry["readings"]) + "\n"
    for sense in entry["senses"]:
        result += "{}: {}\n".format(" ".join(sense["tags"]),
                                    ", ".join(sense["glosses"]))
    return result


def connect(filename=DATABASE_FILENAME):
    """
    Loads database and returns a Database object
    """
    if not path.exists(filename):
        raise FileNotFoundError("Database file not found: " + filename)
    with open(filename, 'r', encoding="utf-8") as f:
        return Database(json.load(f))

def build(filename="JMdict_e.gz", output_filename=DATABASE_FILENAME):
    """
    Builds database from a JMdict gzip or xml file and writes to database
    into output_filename
    Should be used from a command-line
    """
    # NOTE: The JMdict XML file contains XML entities, that are expanded when
    # parsed using Python's stdlib xml.etree.ElementTree like so:
    # ElementTree.parse(f). That is undesired behavior for our use-case. Oshi
    # needs to parse the short entity string, for example &adj-i; should be
    # "adj-i" instead of "adjective (keiyoushi)". That's why it uses an external
    # xml parser: lxml that allows you to specify whether to expand entites.
    extension = path.splitext(filename)[1].lower()
    parser = etree.XMLParser(resolve_entities=False)
    if extension == ".gz":
        with gzip.open(filename) as f:
            tree = etree.parse(f, parser)
    elif extension == ".xml":
        tree = etree.parse(filename, parser)
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
        # last_tags will contain a reference to previously found tags (JMdict
        # specifies that when pos is empty, the previous one should be used)
        last_tags = []
        for xsense in xsenses:
            tags = []
            xtags = xsense.findall('pos') # + xsense.findall('misc')
            for xtag in xtags:
                match = re.search(r'&([\w-]+?);', etree.tostring(xtag, encoding="utf-8").decode('utf-8') or "")
                if match: tags.append(match.group(1))
            glosses = [x.text for x in xsense.findall('gloss')]
            senses.append({"glosses": glosses, "tags": tags or last_tags})
            last_tags = tags
        entry["senses"] = senses
        entries.append(entry)
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False)

if __name__ == "__main__":
    build()
