import gzip, os
import xml.etree.ElementTree as ET

dir = os.path.dirname(__file__)
with gzip.open(os.path.join(dir, 'JMdict_e.gz')) as f:
	root = ET.parse(f).getroot()
	print(root.text)
