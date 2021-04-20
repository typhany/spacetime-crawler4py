import re
from urllib.parse import urlparse, urldefrag, urljoin
import urllib.robotparser  
from collections import defaultdict

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import csv
from bs4 import BeautifulSoup

#global variables
total_tokens = dict()
total_links = []

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    links = []
    parsed = urlparse(url)    

    with open("tokenFreq.csv", "w") as tokencsv:
    #need to count num of unique pages
    #need to save subdomains and count
    #need to get longest page in terms of words

        #print("ok with crawl? -> ", checkRobots(url))
        http_status = resp.status
        #200 means good response -> OK
        if http_status == 200 and not isVisited(url):
            raw_html = resp.raw_response.content
            #parse w/ Beautiful Soup
            soup = BeautifulSoup(raw_html, features = "html.parser")
            

            #parse and tokenize text from url
            text = soup.get_text()
            tokens = tokenizer(text)
            current_tokens = computeTokenFrequency(tokens)
            total_tokens.update(current_tokens)
            #save tokens to file
            writer = csv.writer(tokencsv)
            for word, count in total_tokens.items():
                writer.writerow([word, count])
       

		    #need to check if url has the most tokens

 

		    #find all <a> tags and extract link from href attribute
            for a_tags in soup.findAll("a"):
                hyperlink = a_tags.get("href")
                is_absolute = bool(urlparse(hyperlink).netloc)
                if is_absolute:
                    #only keep links discarding the fragment part
                    no_fragment = urldefrag(hyperlink)[0]
                    total_links.append(no_fragment)
                    links.append(no_fragment)
                else: #combine relative link w/ domain
                    full_hyperlink = urljoin(url, hyperlink)
                    no_fragment = urldefrag(full_hyperlink)[0]
                         
                    total_links.append(no_fragment)
                    links.append(no_fragment)

        else:
            return []
    
    return links

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
    if url in total_links:
        return True
    return False

def isTrap(url):
    #check if url is a trap
    parsed = urlparse(url)

    #(1) path too long (aka infinitely iterating thru blog posts)
    split_path = (parsed.path).split("/")
    if len(split_path) > 4:
        return True

    #(2) does parsed contain any unique keywords
    trapwords = ["?replytocom=", "/tag/", "mailto:"]
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
