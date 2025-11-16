import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://environnement.brussels/pro/gestion-environnementale/gerer-les-dechets/parcours-dechets-professionnels-reduire-trier-et-gerer-vos-dechets-bruxelles"
response = requests.get("url")

html = response.text

soup = BeautifulSoup(html, "html.parser")

pdf_urls = []    

for a in soup.find_all("a", href=True):
    href = a["href"]

    if href.lower().endswith(".pdf"):
        pdf_url = urljoin(url, href)
        pdf_urls.append(pdf_url)

for u in pdf_urls:
    print("pdf: ", u)