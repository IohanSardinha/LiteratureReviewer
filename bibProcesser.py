import bibtexparser
from habanero import counts
import datetime

def getLibrary(file):
    library = bibtexparser.loads(file["content"])
    return library

def getEntries(file):
    return getLibrary(file).entries

def mergeEntries(entriesList):
    entries = []
    for e, _ in entriesList:
        entries += e

    entriesHash = {}
    i = 0
    repeated = 0
    for e in entries:
        if "doi" in e and e["doi"] in entriesHash:
            repeated += 1
            if "times-cited" in e:
                if (not "times-cited" in entriesHash[e["doi"]]) or (e["times-cited"] > entriesHash[e["doi"]]["times-cited"]):
                    entriesHash[e["doi"]] = e
        
        elif not "doi" in e:
            entriesHash[i] = e
            i += 1
        else:
            entriesHash[e["doi"]] = e
    
    return addCitationByYear(list(entriesHash.values())), repeated

def orderEntries(e, key):
    return e[key] if key in e else 0

def sortEntries(entries, key, reverse=True):
    return sorted(entries, key=lambda e: orderEntries(e, key), reverse=reverse)

def addCitationByYear(entries):
    for e in entries:
        if ("times-cited" in e) and ("year" in e):
            e["citation-per-year"] = int(e["times-cited"])/(datetime.datetime.today().year+1-int(e["year"]))
    
    entries = sorted(entries, key=lambda e: orderEntries(e, "year"), reverse=True)
    entries = sorted(entries, key=lambda e: orderEntries(e, "citation-per-year"), reverse=True)

    return entries

def lacksTimeCited(entriesList):
    count = 0
    for entries,_ in entriesList:
        for entry in entries:
            if (not "times-cited" in entry) and ("doi" in entry):
                count += 1
    
    return count

def importCitations(entriesList):
    for entries,_ in entriesList:
        for entry in entries:
            if "doi" in entry:
                entry["times-cited"] = str(counts.citation_count(doi=entry["doi"]))

def getEntriesKeys(entries):
    keys = set()
    for entry in entries:
        for key in entry.keys():
            keys.add(key)
    
    return sorted(list(keys))

def createNewKey(name, expression, entries):
    failed = 0
    for e in entries:
        try:
            e[name] = eval(expression)
        except:
            failed += 1
    
    if failed == len(entries):
        return False
    return True