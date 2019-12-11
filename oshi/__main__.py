"""
oshi -- Japanese grammar tester
"""
import gzip
import os
from lxml import etree

WORKING_DIRECTORY = os.path.dirname(__file__)
tree = None
with gzip.open(os.path.join(WORKING_DIRECTORY, 'JMdict_e.gz')) as f:
    tree = etree.parse('JMdict_e.xml')
# assert isinstance(tree, etree.ElementTree)
print(tree.docinfo.internalDTD)
