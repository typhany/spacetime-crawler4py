import re
from urllib.parse import urlparse, urldefrag, urljoin
import urllib.robotparser  
from collections import defaultdict

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import csv
from bs4 import BeautifulSoup

import shelve


#global variables
max_tokens_in_url = 0
unique_subdomains = set()
visited_links = set()

#shelves to save tokens, longest page, subdomains in ics.uci.edu domain, unique pages
#tokenfile = shelve.open("tokenFreq.db", writeback = True)
#longestPage = shelve.open("longestPage.db", writeback = True)
#ics_subdomains = shelve.open("ics_subdomains.db", writeback = True)
#uniquePages = shelve.open("uniqueURLs.db", writeback = True)


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    visited_links.add(url)
    links = []
    parsed = urlparse(url)    

    http_status = resp.status
    if http_status >= 200 and http_status <=202: 
        raw_html = resp.raw_response.content

        #parse html w/ Beautiful Soup
        soup = BeautifulSoup(raw_html, features = "html.parser")
            
        #parse and tokenize text from url
        text = soup.get_text()
        tokens = tokenizer(text)
        current_tokens = computeTokenFrequency(tokens)
        #save tokens to tokenfile shelve db
        syncTokenFile(current_tokens)       
        
        #check if it has more tokens than the last
        global max_tokens_in_url
        num_tokens = len(current_tokens)
        if num_tokens > max_tokens_in_url:
            max_tokens_in_url = num_tokens
            url_with_max_tokens = url
            #save page w/ most amount of tokens
            syncLongestPage(num_tokens, url)            

        found_ics_subdomains = []
		#find all <a> tags and extract link from href attribute
        for a_tags in soup.findAll("a"):
            hyperlink = a_tags.get("href")

            #check if path is absolute or relative 
            is_absolute = bool(urlparse(hyperlink).netloc)
            if is_absolute:
                no_fragment = urldefrag(hyperlink).url
            else: #combine relative link w/ domain(netloc)
                full_hyperlink = urljoin(url, hyperlink)
                no_fragment = urldefrag(full_hyperlink).url
            links.append(no_fragment)
            #syncUniqueLinks(
            domain = urlparse(no_fragment).netloc
            if "ics.uci.edu" in domain:
                # unique_subdomains.add(domain)
                found_ics_subdomains.append(domain)
        #save pages within ics.uci.edu domain
        syncICSSubdomains(found_ics_subdomains)       

    else:
        return []
    
    return links

##### helper functions #####

def tokenizer(text):
    result = []

    tokens = word_tokenize(text)
    stopwords_list = stopwords.words('english')

    for t in tokens:
        if t not in stopwords_list:
            result.append(t)

    return result

	# tokens = []
	# split_text = text.split()
	# for word in split_text:
	# 	tokens.append(word.lower())
	# return tokens


def computeTokenFrequency(tokens):
    token_dict = defaultdict(int)
    for t in tokens:
        token_dict[t] += 1
    return token_dict

def syncTokenFile(token_dict):
    tokenfile = shelve.open("tokenFreq.db", writeback = True)
    for token, count in token_dict.items():
        if token not in tokenfile:
             tokenfile[token] = count
        else:
             tokenfile[token] += count
    tokenfile.sync()
    tokenfile.close()

def syncLongestPage(token_count, url):
    longestpage = shelve.open("longestPage.db", writeback = True)
    longestpage["token_count"] = token_count
    longestpage["url"] = url
    longestpage.sync()
    longestpage.close()

def syncICSSubdomains(subdomain_list):
    if subdomain_list:
        ics_subdomains = shelve.open("ics_subdomains.db", writeback = True)
        for sub in subdomain_list:
            if sub not in ics_subdomains:
                ics_subdomains[sub] = 1
            else:
                ics_subdomains[sub] += 1
        ics_subdomains.sync()
        ics_subdomains.close()
'''
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
'''

def isVisited(url):
    #check if url has been visited or not
    #return bool
    return url in visited_links
    #if url in visited_links:
    #    return True
    #return False

def isTrap(url):
    #check if url is a trap
    parsed = urlparse(url)

    #(1) path too long (aka infinitely iterating thru blog posts)
    split_path = (parsed.path).split("/")
    if len(split_path) > 4:
        return True

    #(2) does parsed contain any unique keywords
    trapwords = ["?replytocom=", "?share=", "mailto:", "/pdf/"]
    if any(tword in url for tword in trapwords):
        return True

    #(3) ???

    else:
        return False
    

def is_valid(url):
    #valid domains 
    pattern1 = re.compile(r".*\.(?:ics|cs|informatics|stat)\.uci\.edu")
    pattern2 = re.compile(r"today\.uci\.edu/department/information_computer_sciences/.*")

    try:
        parsed = urlparse(url) #returns parseresult(scheme, netloc, path, params, query, fragment)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if not re.match(pattern1, parsed.netloc) and not re.match(pattern2, parsed.netloc + parsed.path):
            return False

        if isTrap(url):
            return False
        if isVisited(url):
            return False

        #return not re.match(
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
        
            return False
       
        #if re.match(pattern1, parsed.netloc):
        #    return True
        #if re.match(pattern2, parsed.netloc + parsed.path):
        #    return True 

        else:
            return True





    except TypeError:
        print ("TypeError for ", parsed)
        raise
