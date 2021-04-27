import json
from collections import defaultdict
from urllib.parse import urlparse

print("token frequency")
with open("tokenFreq.json", "r") as jsonfile:
    data = json.load(jsonfile)

top50 = sorted(data.items(), key = lambda item: item[1], reverse = True)[0:50]
for token, count in top50:
    print(token, "->", count)



print("\nics subdomains")

with open("visited_links.txt", "r", encoding = "utf-8") as file:
    data = file.readlines()

print("# unique links:", len(data))


ics_subdomains = defaultdict(int)
for hyperlink in data:
    hyperlink = hyperlink.rstrip("\r\n")
    if "ics.uci.edu" in hyperlink:
        netloc = urlparse(hyperlink).netloc
        ics_subdomains[netloc.lower()] += 1


sorted_subdomains = sorted(ics_subdomains.items(), key = lambda item: item[0])
for subdomain, count in sorted_subdomains:
    print(subdomain, "->", count)

print("\n# subdomains: ", len(sorted_subdomains))
