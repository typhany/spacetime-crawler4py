import re
from urllib.parse import urlparse
import urllib.robotparser  

#import requests

from bs4 import BeautifulSoup


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation requred.
    #print(url, resp)

    #print("ok with crawl? -> ", checkRobots(url))
    http_status = resp.status
    #200 means good response -> OK
    if http_status == 200:
        raw_html = resp.raw_response.content
         #parse w/ Beautiful Soup
        soup = BeautifulSoup(raw_html, features = "html.parser")
        #print(soup.get_text())
        #print(type(soup.get_text()))
        
        text = soup.get_text()
        print(tokenizer(text))


        #parse and tokenize text from url
        
		#find all <a> tags and extract link from href attribute
        # for a_tags in soup.findAll("a"):
        #     hyperlink = a_tags["href"]
        #     print(hyperlink)


    else:
        pass
    
    return list()

def tokenizer(text):
	tokens = []
	#punctuated_tokens = []
	split_text = text.split()

	#pattern = '[^a-z0-9]+'
	for word in split_text:
		# if word.isalnum():
		tokens.append(word.lower())
		# else:
		# 	punctuated_tokens.append(word)

	# print(tokens)
	# print(punctuated_tokens)

	return tokens


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
