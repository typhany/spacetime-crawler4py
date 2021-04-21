import re
from urllib.parse import urlparse, urldefrag, urljoin
import urllib.request
import urllib.robotparser  
from collections import defaultdict

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import csv
from bs4 import BeautifulSoup
import requests
import shelve
import time

#global variables
max_tokens_in_url = 0
unique_subdomains = set()
visited_links = set()
found_ics_subdomains = []
current_links = []

def scraper(url, resp):
    result = []
    links = extract_next_links(url, resp)

    #remove fragment from link and check if under ics.uci.edu domain
    if links:
        for hyperlink in links:
            nofragment = urldefrag(hyperlink).url
            result.append(nofragment)
         
            if "ics.uci.edu" in nofragment:
                found_ics_subdomains.append(nofragment)
        syncICSSubdomains(found_ics_subdomains)


        return [link for link in result if is_valid(link)]
    else:
        return []

def extract_next_links(url, resp):
    #print(url, resp.status)
    links = []

    if resp.status == 200 or resp.status == 201 or resp.status == 202:
        print("status: ", resp.status, "--- will scrape")
        raw_html = resp.raw_response.content
        soup = BeautifulSoup(raw_html, features = "html.parser")
        
        visited_links.add(url)
        with open("visited_links.txt", "a") as file:
            file.write(url + "\n") 
        ### 
        
        text = soup.get_text()
        tokens = tokenizer(text) #total words
        unique_words = set(tokens) #unique words
        #current_tokens = computeTokenFrequency(tokens)

        #ratio to check if enough content to scrape
        if len(tokens) == 0 or len(unique_words)/len(tokens) <= 0.25:
            print("not content rich"))

        else:
            current_tokens = computeTokenFrequency(tokens)
            syncTokenFile(current_tokens)       
 
            global max_tokens_in_url
            num_tokens = len(current_tokens)
            if num_tokens > max_tokens_in_url:
                max_tokens_in_url = num_tokens
                syncLongestPage(num_tokens, url)
     
        ###  
            start_time = time.time()
     
            for a_tags in soup.findAll("a"):
                 hyperlink = a_tags.get("href")
                 is_absolute = bool(urlparse(hyperlink).netloc)
                 if is_absolute:
                     links.append(hyperlink)
                 else:
                     full_hyperlink = urljoin(url, hyperlink)
                     links.append(full_hyperlink)

            current_time = time.time()  
            if (current_time - start_time > 6):
                return []
            else:
                return links  



    else:
        print("status: ", resp.status, "--- valid url but will not scrape") 
    
    #return links                    



    '''
    #visited_links.add(url)
    links = []
    parsed = urlparse(url)    

    response = requests.get(url, allow_redirects = False)
    http_status = response.status_code #resp.status
    
    try:
    
        if (http_status == 200) or (http_status == 201) or (http_status == 202): #http_status >= 200 and http_status <=202:
            print(http_status, (type(http_status))) 
            #save links visited to txt file
            visited_links.add(url)
            with open("visited_links.txt", "a") as file:
                file.write(url + "\n")

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

            #found_ics_subdomains = []
		    #find all <a> tags and extract link from href attribute
            #possibly another loop??

            for a_tags in soup.findAll("a"):
                hyperlink = a_tags.get("href")
                
                is_absolute = bool(urlparse(hyperlink).netloc)
                if is_absolute:
                    links.append(hyperlink)
                else:
                    links.append(url + hyperlink)

                #print(hyperlink)
                #links.append(hyperlink)
                #check if path is absolute or relative 
                #is_absolute = bool(urlparse(hyperlink).netloc)
                #print(hyperlink, is_absolute)
                
                #if is_absolute:
                 #   print("yes!!")
                  #  no_fragment = urldefrag(hyperlink).url
                    #print(no_fragment)
                    #links.append(no_fragment)
                    #print("abs links: ", links)
                    #checkSubdomain(no_fragment)
                    #print("abs:", no_fragment)
                #else: #combine relative link w/ domain(netloc)
                #    full_hyperlink = urljoin(url, hyperlink)
                #    no_fragment = urldefrag(full_hyperlink).url
                   
                #    links.append(full_fragment)
                #    checkSubdomain(full_fragment)
                    #print("rel:", full_fragment)
             
               #syncUniqueLinks(
               # domain = urlparse(no_fragment).netloc
               # if "ics.uci.edu" in domain:
               #    unique_subdomains.add(domain)
               #     found_ics_subdomains.append(domain)
            #save pages within ics.uci.edu domain
           # syncICSSubdomains(found_ics_subdomains)
      

    except Exception as error:
        pass

    #sleep(0.5)
    #print(links)
    return links
    '''


def checkSubdomain(url):
    domain = urlparse(url).netloc
    if "ics.uci.edu" in domain:
        found_ics_subdomains.append(subdomain)
    syncICSSubdomains(found_ics_subdomains)
    


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
    alreadyVisited = []
    if ("visited_links.txt"):
        with open("visited_links.txt", "r", encoding = "utf-8") as file:
            for line in file:
                alreadyVisited.append(line.rstrip())
    return url in alreadyVisited
    #check if url has been visited or not
    #return bool

    #return url in visited_links
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

    #(2) does url contain any unique keywords
    trapwords = ["?replytocom=", "?share=", "mailto:", "/pdf/", ".pdf", ".DS_STORE", "/events/", "/download/download.inc"]
    calendars = re.compile(r"\/events\/[0-9]{4}-[0-9]{2}-[0-9]{2}")
    genomes = re.compile(r"\/(cgo|pgo|fgo)\/(p|f|c)[0-9]")
    if any(tword in url for tword in trapwords):
        return True
    if re.match(calendars, parsed.path):
        return True
    if bool(genomes.search(parsed.path)):
        return True


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
            + r"|png|tiff?|mid|mp2|mp3|mp4|war|img"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ppsx|apk" #added ppsx, apk, war, img
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
