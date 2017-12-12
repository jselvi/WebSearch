#!/usr/bin/python
# Python Script that query Bing for search Virtual Host's related to a IP range
# Jose Selvi - jselvi[a.t]pentester[d0.t]es - http://www.pentester.es
# Version 0.1 - 14/Oct/2009 - Search at Bing and show hostnames
# Version 0.2 - 03/Feb/2010 - Input now allow big networks
# Version 1.0 - 23/Aug/2014 - Updated to Azure 
# Version 1.1 - 27/Sep/2016 - Updated to Cognitive

# Importing
from optparse import OptionParser
from sets import Set
import sys
import re
import signal
import urllib
import urllib2
import json
import os
import socket

# Bing API Key. Avoid typing it down each time. Be careful when sharing this script.
# https://www.microsoft.com/cognitive-services/en-us/subscriptions (Bing Search - Free)
hardcoded_key = ""

# Convert IP to number
def ip2num(ipvect):
    ipnum = (ipvect[0]<<24) | (ipvect[1]<<16) | (ipvect[2]<<8) | (ipvect[3])
    return ipnum

# Convert number to IP
def num2ip(ipnum):
    ip1 = ipnum >> 24
    ip2 = ipnum >> 16 & 0xFF
    ip3 = ipnum >> 8 & 0xFF
    ip4 = ipnum & 0xFF
    return [int(ip1), int(ip2), int(ip3), int(ip4)]

# Query BING
def query_bing(key,query):
    query = urllib.quote(query)
    user_agent = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
    url = 'https://api.cognitive.microsoft.com/bing/v7.0/search?q='+query+'&count=50&safeSearch=off'
    request = urllib2.Request(url)
    request.add_header('Ocp-Apim-Subscription-Key', key)
    request.add_header('User-Agent', user_agent)
    request_opener = urllib2.build_opener()
    response = request_opener.open(request) 
    response_data = response.read()
    json_result = json.loads(response_data)
    if 'webPages' in json_result and 'value' in json_result['webPages']:
        result_list = json_result['webPages']['value']
    else:
        result_list = []
    return result_list

# Get Parameters
usage = "usage: %prog [options]"
parser = OptionParser(usage=usage)
parser.add_option("-H", "--hosts", type="string", dest="ip_range", help="IP range: 192.168.0.1-192.168.1.255")
parser.add_option("-K", "--key", type="string", dest="bing_api", default=hardcoded_key, help="Bing API key")
(options, args) = parser.parse_args()
if len(options.bing_api) == 0:
    print "Set up a Bing API Key: https://www.microsoft.com/cognitive-services/en-us/subscriptions (Bing Search - Free)"
    exit()
if not options.ip_range:
    parser.print_help()
    exit()

# Testing parameter
ipre = re.compile('[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+-[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')
m = ipre.match( options.ip_range )
if not m:
    parser.print_help()
    exit()

# Splitting IPs pieces
entrada = options.ip_range
[aux1, aux2] = entrada.split("-")
ipbegin = aux1.split(".")
iplast = aux2.split(".")

# Testing sense
for i in range(0,4):
    ipbegin[i] = int(ipbegin[i])
    iplast[i] = int(iplast[i])
    if not ( 0<=ipbegin[i]<=255 and 0<=iplast[i]<=255 ):
        print "ERROR! Wrong IP Address"
        exit()

# Casting IP Address to Integer
num_ipbegin = ip2num(ipbegin)
num_iplast = ip2num(iplast)

# Testing Begin is low than Last
if ( num_iplast < num_ipbegin ):
    print "ERROR! Last IP mus be higher than Begin IP"
    exit()

# For each IP, we're looking for hostnames in Bing
try:
    for num_IP in range(num_ipbegin, num_iplast+1):
        # Translate num_IP to String
        vectIP = num2ip(num_IP)
        IP = str(vectIP[0])+"."+str(vectIP[1])+"."+str(vectIP[2])+"."+str(vectIP[3])
        # Empty exceptions list
        deleted = ""
        hosts = Set()
        # Querying Bing
        try:
            oldlen = len(hosts)
            sys.stderr.write("Searching hostnames for: "+IP+"\n")
            response = query_bing(options.bing_api,"ip:"+IP)
            while len(response) > 0:
                oldlen = len(hosts)
                for res in response:
                    if 'displayUrl' in res:
                        hostname_vect = res['displayUrl'].split("/")
                        if hostname_vect[0].startswith("http"):
                            hostname = hostname_vect[2]
                        else:
                            hostname = hostname_vect[0]
                        if hostname not in hosts:
                            print hostname
                            hosts.add( hostname )
                            deleted = deleted + " -site:" + hostname
                # If no new hosts, break
                newlen = len(hosts)
                if oldlen == newlen:
                    break
                response = query_bing(options.bing_api, "ip:" + IP + deleted )
        except IOError, e:
            sys.stderr.write("ERROR! " + IP + " HOSTNAME'S LIST WAS NOT FULLY COMPLETE!\n")
except Exception, e:
    sys.stderr.write("Exiting...")
