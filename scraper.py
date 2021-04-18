import re
from urllib.parse import urlparse
import urllib.robotparser  
from collections import defaultdict

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
#import requests

from bs4 import BeautifulSoup

#global variables
total_tokens = dict()
total_links = []

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
	links = []
    # Implementation requred.
    #print(url, resp)

    #print("ok with crawl? -> ", checkRobots(url))
    http_status = resp.status
    #200 means good response -> OK
    if http_status == 200:
        raw_html = resp.raw_response.content
         #parse w/ Beautiful Soup
        soup = BeautifulSoup(raw_html, features = "html.parser")

        #parse and tokenize text from url
        text = soup.get_text()
        tokens = tokenizer(text)
        current_tokens = computeTokenFrequency(tokens)
        total_tokens.update(current_tokens)
        
		#find all <a> tags and extract link from href attribute
        for a_tags in soup.findAll("a"):
            hyperlink = a_tags["href"]
            total_links.append(hyperlink)
            #print(hyperlink)


    else:
        pass
    
    return list()

def tokenizer(text):
	result = []

	tokens = word_tokenize(text)
	stopwords = stopwords.words('english')

	for t in tokens:
		if t not in stopwords:
			result.append(t)

	return result

	# tokens = []
	# split_text = text.split()
	# for word in split_text:
	# 	tokens.append(word.lower())
	# return tokens


def computeTokenFrequency(tokens):
	token_dict = defaultdict(int):
	for t in tokens:
		token_dict[t] += 1
	return token_dict

def computeLinkCount(links):
	domains_set = set()
	subdomains_set = defaultdict(int)
	
	for url in links:
		domain = urlparse(url).netloc
		domains_set.add(domain)
		subdomains_set[url] += 1

	for sd in subdomains_set.keys():
		if sd in domains_set:
			del subdomains_set[sd]

	return domains_set, subdomains_set


def isVisited(url):
    #check if url has been visited or not
    #return bool
	pass

#for extra credit +1 point
# def checkRobots(url):
#     #given url, parse robots.txt to see if it is ok to crawl or not
#     robots_url = url + "/robots.txt"
#     robot_page = urllib.robotparser.RobotFileParser()
#     robot_page.set_url(robots_url)
#     robot_page.read()

#     #check if it is ok to crawl
#     validity = robot_page.can_fetch("*", robots_url)
#     return validity







def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
