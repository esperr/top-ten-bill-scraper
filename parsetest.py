import requests
import xml.etree.ElementTree as etree
from bs4 import BeautifulSoup

r = requests.get("https://www.congress.gov/bill/117th-congress/senate-bill/1260")
bill_html = BeautifulSoup(r.text, "html.parser")

status_table = bill_html.find(table)
print(status_table)


#for item in root.findall('.//item'):
#    print("found one!")
