import PAsearchSites
import urllib2 as urllib
import PAgenres
import PAutils

def getDatafromAPI(url):
    req = PAutils.HTTPRequest(url)

    if req:
        return req.json()['data']
    return req

getDatafromAPI('https://www.blacked.com/api/search?q=Addicted')