import requests
from tqdm import tqdm
import json
import re
import queue
import os
import threading
import subprocess
import pickle
import time
import shelve
import signal
import atexit
from collections import namedtuple
signal.signal(signal.SIGTERM, lambda num, frame: sys.exit(0))
Player = namedtuple('Player', ['name', 'code', 'ranks'])
Player.__eq__ = lambda x,y: x.name == y.name
Player.__hash__ = lambda x: hash(x.name)
token_url = "https://www.warcraftlogs.com/oauth/token"
api_url = "https://classic.warcraftlogs.com/api/v2/client"
session = requests.Session()

#Every class and their specs used in warcraftlogs
class_specs = {"Druid": ["Balance", "Feral", "Guardian", "Restoration", "Warden", "Dreamstate"], "Hunter": ["BeastMastery", "Marksmanship", "Survival"], "Mage": ["Arcane", "Fire", "Frost"], "Paladin": ["Holy", "Protection", "Retribution", "Justicar"], "Priest": ["Discipline", "Holy", "Shadow", "Smiter"], "Rogue": ["Assassination", "Combat", "Subtlety"], "Shaman": ["Elemental", "Enhancement", "Restoration"], "Warlock": ["Affliction", "Demonology", "Destruction"], "Warrior": ["Arms", "Fury", "Protection", "Gladiator", "Champion"]}
healing_specs = {"Restoration", "Dreamstate", "Holy", "Discipline", "Healing"}
#zones = ["1007", "1012", "1008", "1010", "1011"]
zone_abbreviations = {"Karazhan": "K", "Gruul_Mag":"G", "SSC_TK":"T", "BT_MH":"H", "ZA":"Z"}

#First boss in each TBC raid excluding Sunwell.
encounters = ["652", "1189", "649", "651", "623", "730", "601", "618"]

#Current partition is 5 - P3.5 & P4
partition = 5

factions = {"alliance": 0, "horde": 1}
timer = False
timer_thread = None
access_token = None

db = shelve.open('appstate')

@atexit.register
def exit_handler():
    global timer_thread
    db.close()
    if timer_thread != None:
        timer_thread.cancel()

def renew_tokens():
    with open('creds.txt') as creds:
        client_id, client_secret = creds.readline().strip().split(",")
        data = {'grant_type': 'client_credentials'}
        token_response= requests.post(token_url, data=data, allow_redirects=False, auth=requests.auth.HTTPBasicAuth(client_id, client_secret))
        tokens = json.loads(token_response.text)
        #access_token = tokens['access_token']
        session.headers.update({'Authorization': 'Bearer ' + tokens['access_token']})

def stop_timer():
    global timer
    print("Stopping Timer")
    timer = False

def query_wcl(query):
    global timer, timer_thread
    try: 
        response = session.post(api_url, json={"query": query})
        if response.status_code == 429:
            print("API Point limit exceeded waiting for point reset")
            if timer_thread == None:
                timer = True
                timer_thread = threading.Timer(3600, stop_timer) #Assuming no API calls have been made outside of this script
                timer_thread.start()
            timer_thread.join()
            timer_thread = None
            print("API Points should have reset, resuming operation.")
            return query_wcl(query)
        elif response.status_code == 401:
            renew_tokens()
            return query_wcl(query)
        elif response.status_code != 200:
            return query_wcl(query)
        else:
            if response.text == "" or response.text.startswith("No class set for this character"):
                return None
            if timer_thread == None:
                timer = True
                timer_thread = threading.Timer(3600, stop_timer) #Assuming no API calls have been made outside of this script
                timer_thread.start()
            return json.loads(response.text)
    except:
        print_except(query, response)
        return query_wcl(query)

def print_except(q, r):
    print("Error occurred for query")
    print(q)
    print("Received response")
    print(r)
    exit()

def get_server_ids(servers):
    query = "query { worldData { "
    for server in servers:
        slug, region = server['name'].lower().replace(' ', '-'), server['region'].lower()
        query += f"{slug.replace('-','_')}: server(slug:\"{slug}\" region: \"{region}\")" + "{ id },"
    query += "}}"
    response = json.loads(query_wcl(query))
    return response

def update_needed(p, slug, region):
    query = "query { characterData { character(name: \"%s\", serverSlug: \"%s\", serverRegion: \"%s\") { recentReports(limit: 1) { data { code } } } } }" % (p.name, slug, region)
    response = query_wcl(query)

    if response["data"]["characterData"]["character"]:
        return response["data"]["characterData"]["character"]["recentReports"]["data"][0]["code"] != p.code
    else:
        return False

def query_player_rankings(p, slug, region, metric):
    query = "query { characterData { character(name: \"%s\", serverSlug: \"%s\", serverRegion: \"%s\") { Karazhan: zoneRankings(zoneID: 1007, partition: -1, metric: %s), Gruul_Mag: zoneRankings(zoneID: 1008, partition: -1, metric: %s), SSC_TK: zoneRankings(zoneID: 1010, partition: -1, metric: %s), BT_MH: zoneRankings(zoneID: 1011, partition: -1, metric: %s), ZA: zoneRankings(zoneID: 1012, partition: -1, metric: %s), recentReports(limit: 1){ data { code } } } } }" % (p.name, slug, region, metric, metric, metric, metric, metric)
    return query_wcl(query)

def get_player_info(p, slug, region):
    response = query_player_rankings(p, slug, region, "dps")
    if response == None:
        return None

    if response["data"]["characterData"]["character"] == None or response["data"]["characterData"]["character"]["recentReports"]["data"] == None:
        return None
    code = response["data"]["characterData"]["character"]["recentReports"]["data"][0]["code"]
    possibly_healer = False
    zones = ["Karazhan", "Gruul_Mag", "SSC_TK", "BT_MH", "ZA"]
    healing_ranks = None
    if any([x["spec"] in healing_specs for zone in zones for x in response["data"]["characterData"]["character"][zone]["allStars"]]):
        healing_ranks = query_player_rankings(p, slug, region, "hps")
    text = "|"
    for zone in zones:
        text += zone_abbreviations[zone] + " "
        done = sum([1 for x in response["data"]["characterData"]["character"][zone]["rankings"] if x["totalKills"] > 0])
        possible = len(response["data"]["characterData"]["character"][zone]["rankings"])
        progress = add_color_code((done/possible)*100) + "%i/%i" % (done, possible)
        text += progress + " "

        if response["data"]["characterData"]["character"][zone]["bestPerformanceAverage"] != None:
            if healing_ranks != None and all([x["spec"] in healing_specs for x in response["data"]["characterData"]["character"][zone]["allStars"]]):
                best_avg_h = healing_ranks["data"]["characterData"]["character"][zone]["bestPerformanceAverage"]
                median_avg_h = healing_ranks["data"]["characterData"]["character"][zone]["medianPerformanceAverage"]
                h_ranks = add_color_code(best_avg_h) + "{:.1f}".format(best_avg_h) +  "%/" + add_color_code(median_avg_h) + "{:.1f}".format(median_avg_h) + "% (HPS)"
                text += h_ranks
            else:
                best_avg = response["data"]["characterData"]["character"][zone]["bestPerformanceAverage"]
                median_avg = response["data"]["characterData"]["character"][zone]["medianPerformanceAverage"]
                d_ranks = add_color_code(best_avg) + "{:.1f}".format(best_avg) +  "%/" + add_color_code(median_avg) + "{:.1f}".format(median_avg) + "% (DPS)"
                text += d_ranks + " "

                if healing_ranks != None:
                    best_avg_h = healing_ranks["data"]["characterData"]["character"][zone]["bestPerformanceAverage"]
                    median_avg_h = healing_ranks["data"]["characterData"]["character"][zone]["medianPerformanceAverage"]
                    h_ranks = add_color_code(best_avg_h) + "{:.1f}".format(best_avg_h) +  "%/" + add_color_code(median_avg_h) + "{:.1f}".format(median_avg_h) + "% (HPS)"
                    text += h_ranks
        text += "|"

    return Player(p.name, code, text)

def filter_players(rankings, faction):
    return set(map(lambda x: Player(x["name"], None, None), filter(lambda x: x["faction"] == faction, rankings)))

def get_players_census(name, slug, region, faction):
    idf = '_'.join([slug, region, faction])
    res = subprocess.check_output(["lua", "convert_census_data.lua", name, faction]).decode('UTF-8')
    db[idf] |= {Player(x, None, None) for x in res.strip().split('\n')}

def get_ranked_players(slug, region, faction, encounter, cl, spec, metric, page):
    idf = '_'.join([slug, region, faction])
    query = "query{worldData { encounter(id: %s) { characterRankings(serverSlug: \"%s\", serverRegion: \"%s\", className: \"%s\", specName: \"%s\", includeCombatantInfo: false, partition: %s, metric: %s), } } }" % (encounter, slug, region, cl, spec, partition, metric)
    response = query_wcl(query)
    character_rankings = None
    if response != None:
        character_rankings = response["data"]["worldData"]["encounter"]["characterRankings"]
    if character_rankings["rankings"] != None:
        db[idf] |= filter_players(character_rankings["rankings"], faction)
    if character_rankings["hasMorePages"] == True and page < 5: 
        # 5 is the page limit of the API for server rankings
        get_ranked_players(slug, region, faction, encounter, cl, spec, partition, metric, page + 1)

def get_players_wcl(slug, region, fac):
    print(f"Starting initial scan of Warcraft Logs for players on {slug}-{region} {fac}")
    i, e, c, s = 0, 0, 0, 0
    idf = '_'.join([slug, region, faction])
    if idf + '_progress' in db.keys():
        e, c, s = db[idf + '_progress']

    for encounter in encounters[e:]:
        e = 0
        for cl in list(class_specs.keys())[c:]:
            c = 0
            c_players = set()
            for spec in class_specs[cl][s:]:
                s = 0
                print(f"Processing {spec} {cl}s on encounter {encounter}")
                if spec in healing_specs:
                    get_ranked_players(slug, region, faction, encounter, cl, spec, "hps", 1)
                else:
                    get_ranked_players(slug, region, faction, encounter, cl, spec, "dps", 1)
                db[idf + '_progress'] = (e+1, c+1, s+1)
                s += 1
            c += 1
        e += 1
    del db[idf + '_progress']
    print(f"Finished initial scan of Warcraft Logs for players on {slug}-{region} {faction}")

def add_color_code(percent):
    if percent == 100:
        return "A"
    elif percent >= 99:
        return "S"
    elif percent >= 95:
        return "L"
    elif percent >= 85:
        return "N"
    elif percent >= 75:
        return "E"
    elif percent >= 50:
        return "R"
    elif percent >= 25:
        return "U"
    return "C"

def write_target(server_name, filename, userdata):
    path = "../WCLRanks/Data/"

    if not os.path.exists(path):
        os.mkdir(path)

    f = open( path + filename + ".lua", 'w+')
    f.write("if(GetRealmName() == \"%s\")then\nWP_Database = {\n" % server_name)

    for p in userdata:
        f.write("[\"%s\"] = \"%s\",\n" % (p.name, p.ranks))

    f.write("}\nend")
    f.close()

def app_loop():
    while True:
        start = time.time()
        with open('targets.json') as t:
            target = json.load(t)
            for server in target.get("servers"):
                print(f"Processing server {server}")
                slug, region, faction = server.get("name").lower().replace(" ", "-"), server.get("region").lower(), server.get("faction").lower()
                idf = '_'.join([slug, region, faction])
                if idf not in db['initialized_servers']:
                    get_players_census(server.get("name"), slug, region, faction)
                    get_players_wcl(slug, region, faction)
                else:
                    get_players_census(server.get("name"), slug, region, faction)
                if idf + '_updated' in db.keys():
                    to_scan = db[idf] - db[idf + '_updated']
                else:
                    to_scan = db[idf]
                    db[idf + '_updated'] = set()
                

                i = 1
                for player in tqdm(to_scan):
                    if update_needed(player, slug, region):
                        updated_player = get_player_info(player, slug, region)
                        if updated_player != None: 
                            db[idf + '_updated'] = {updated_player} | db[idf + '_updated']
                        else:
                            db[idf + '_updated'] = {player} | db[idf + '_updated']
                    i += 1
                db[idf] = db[idf + '_updated'] | db[idf]
                del db[idf + '_updated']
                write_target(server.get("name"), server.get("name"), db[idf])

        #Bump version, push to repo
            
        if 86400 - (time.time() - start) > 0: 
            time.sleep(86400 - (time.time() - start))
            
def main():
    renew_tokens()
    app_loop()
    if timer_thread:
        timer_thread.cancel()

if __name__ == "__main__":
    main()
