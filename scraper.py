import re
from urllib.parse import urlparse, urldefrag, urljoin
import urllib.request
import urllib.robotparser  
from collections import defaultdict

from nltk.tokenize import TweetTokenizer

import csv
from bs4 import BeautifulSoup
import requests
import shelve
import time

import os.path
import json

#global variables
max_tokens_in_url = 0

def scraper(url, resp):
    result = []
    links = extract_next_links(url, resp)
    ics_subdomains = defaultdict(int)
    #remove fragment from link and check if under ics.uci.edu domain
    if links:
        for hyperlink in links:
            nofragment = urldefrag(hyperlink).url
            result.append(nofragment)
            
            #check if hyperlink is under ics.uci.edu domain 
            if "ics.uci.edu" in nofragment:
                hostname = urlparse(nofragment).netloc
                ics_subdomains[hostname] += 1
        syncSubdomains(ics_subdomains)

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
        
        #visited_links.add(url)
        with open("visited_links.txt", "a") as file:
            file.write(url + "\n") 
        ### 

        text = soup.get_text()

        tokens = tokenizer(text) #total words
        unique_words = set(tokens) #unique words
        

        #ratio to check if enough content to scrape
        if len(tokens) < 100 or len(unique_words)/len(tokens) <= 0.25:
            print("not content rich")
            return []

        else:
            current_tokens = computeTokenFrequency(tokens)
            syncTokenFile(current_tokens)
                   
 
            global max_tokens_in_url
            num_tokens = len(current_tokens)
            if num_tokens > max_tokens_in_url:
                max_tokens_in_url = num_tokens
                with open("longestPage.txt", "w") as file:
                    file.write("number of tokens: " + str(num_tokens) + "\n" + "url: " + url + "\n")
                    
     
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
                print("overtime")
                return []
            else:
                print("returning links: ", bool(links))
                return links  



    else:
        print("status: ", resp.status, "--- valid url but will not scrape") 
    
    #return links                    

##### helper functions #####

def syncTokenFile(tokens):
    if os.path.isfile("tokenFreq.json"):
        #update json file
        with open("tokenFreq.json", "r") as readJson:
            data = json.load(readJson)
        
        for k, v in tokens.items():
            if k in data.keys():
                data[k] += v
            else:
                data[k] = v
 
        with open("tokenFreq.json", "w") as writeJson:
            json.dump(data, writeJson)
            
    else:
        #create the json file
        with open("tokenFreq.json", "w") as jsonFile:
            json.dump(tokens, jsonFile)


def syncSubdomains(subdomains):
    #save ics.uci.edu subdomains   
    if os.path.isfile("ics_subdomains.json"):
        #update
        with open("ics_subdomains.json", "r") as readJson:
            data = json.load(readJson)
        
        for k, v in subdomains.items():
            if k in data.keys():
                data[k] += v
            else:
                data[k] = v  
 
        with open("ics_subdomains.json", "w") as writeJson:
            json.dump(data, writeJson)
    else:
        with open("ics_subdomains.json", "w") as jsonFile:
            json.dump(subdomains, jsonFile)


def tokenizer(text):
    result = []

    tokens = TweetTokenizer().tokenize(text)
    stopwords_list = get_stopwords()
    for t in tokens:
        if t not in stopwords_list and t.isalnum():
            result.append(t.lower())

    return result

def get_stopwords():
    stopwords = []
    with open("stopwords.txt", "r", encoding = "utf-8") as file:
        words = file.readlines()
    for sword in words:
        stopwords.append(sword.rstrip("\r\n"))
    return stopwords



def computeTokenFrequency(tokens):
    token_dict = defaultdict(int)
    for t in tokens:
        token_dict[t] += 1
    return token_dict

def isVisited(url):
    alreadyVisited = []
    if ("visited_links.txt"):
        with open("visited_links.txt", "r", encoding = "utf-8") as file:
            for line in file:
                alreadyVisited.append(line.rstrip())
    #print("visited?: ", (url in alreadyVisited))
    return url in alreadyVisited

def isTrap(url):
    #check if url is a trap
    parsed = urlparse(url)

    #(1) path too long (aka infinitely iterating thru blog posts)
    split_path = (parsed.path).split("/")
    if len(split_path) > 4:
        return True

    #(2) does url follow unique patterns, contain keywords to urls that iterate over links or lead to bizzare places
    trapwords = ["?page_id=", "?replytocom=", "?share=", "?ical=", "?tab_files=", "?letter=", 
                  "mailto:", ".pdf", ".DS_STORE", ".Thesis", ".Z", 
                  "/pdf/", "/events/", "/blog/", "/tag/", "/download/"]
    calendars = re.compile(r"\/events\/[0-9]{4}-[0-9]{2}-[0-9]{2}")
    genomes = re.compile(r"\/(cgo|pgo|fgo)\/(p|f|c)[0-9]")
    if any(tword in url for tword in trapwords):
        return True
    if re.match(calendars, parsed.path):
        return True
    if bool(genomes.search(parsed.path)):
        return True


    #(3) if url has "?", "&", or "%" ==> indicates long messy url (? and &) OR redirection (%)
    if "&" in url or "?" in url:
        count = 0
        for char in url:
            if char == "&" or char == "?":
                count += 1
        if count > 1:
            return True

    if "%" in url:
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
            + r"|png|tiff?|mid|mp2|mp3|mp4|mpg|war|img|psp|py|m|pps|bib|odb"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf|ppsx|apk" #added pps, bib, odb, m, psp, py, ppsx, apk, war, img, mpg
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower()):
        
            return False
    

        else:
            return True





    except TypeError:
        print ("TypeError for ", parsed)
        raise
