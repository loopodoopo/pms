# Hibernia Networks - Peering Management System - 2016
# Maikel de Boer - maikel.deboer@hibernianetworks.com

#PeeringDB functions

import requests, ipaddress, os, time, json, logging, ConfigParser

pdb_cache = 86400

def get_as_name(asn):
    #Get asn name by asn
    now = time.time()
    time_ago = now - pdb_cache

    if os.path.isfile('pdb.cache') and os.path.getctime('pdb.cache') > time_ago:
	with open("pdb.cache") as json_file:
            json_data = json.load(json_file)
    else:
        r = requests.get('https://www.peeringdb.com/api/net')
	f = open("pdb.cache", "w")
	f.write(r.text)
	f.close
	get_as_name(asn)
    for x in json_data['data']:
	if str(x['asn']) == str(asn):
	    return x['name']

def build_asn_dict():
    #builds a dictonary for {asn:name} for fast lookup we cache this localy
    asndict = {}
    r = requests.get('https://www.peeringdb.com/api/net')
    json_data = r.json()
    for item in json_data['data']:
        asndict.update({item['asn']: item['name']})
    return asndict

def map_pfx_to_ix(pfx):
    #Map a ip address to a ixid on peering db
    #We go from ip address to prefix to ixid
    #It is important that the correct subnetmask is configured on the router for this function to find anything.
    block = unicode(pfx)
    block = ipaddress.ip_network(block, strict=False)
    block = str(block.with_prefixlen)
    api_data = requests.get('https://www.peeringdb.com/api/ixpfx?prefix=' + block)
    json_data = api_data.json()
    for x in json_data['data']:
       return x['ixlan_id']

def map_id_to_ix(ixlan_id):
    #Map ixid to name
    api_data = requests.get('https://www.peeringdb.com/api/ix?id=' + str(ixlan_id))
    json_data = api_data.json()
    for x in json_data['data']:
        return x['name']

def map_id_to_name(net_id):
    #Map name to id
    api_data = requests.get('https://www.peeringdb.com/api/net?id=' + str(net_id))
    json_data = api_data.json()
    for x in json_data['data']:
        return x['name']

def map_id_to_asn(net_id):
    #map netid to asn
    api_data = requests.get('https://www.peeringdb.com/api/net?id=' + str(net_id))
    json_data = api_data.json()
    for x in json_data['data']:
        return x['asn']

def get_asn_on_ix(ixlan_id):
    #Get all asn's on a ix by ixlan_id
    api_data = requests.get('https://www.peeringdb.com/api/netixlan?ixlan_id=%s&depth=2' % ixlan_id)
    if api_data.status_code == 200:
        json_data = api_data.json()
        return json_data['data']

def get_peeringdb_id(asn):
    #Get peeringdb id for a asn
    api_data = requests.get('https://www.peeringdb.com/api/net?asn=%s' % asn)
    json_data = api_data.json()
    for x in json_data['data']:
        return x['id']

def get_asn_contact(asn):
    #Get mail contacts by asn
    configuration = ConfigParser.ConfigParser()

    configuration.readfp(open('config.cfg'))
    pdbusername = configuration.get('peeringdb', 'username')
    pdbpassword = configuration.get('peeringdb', 'password')

    netid = get_peeringdb_id(asn)

    url = 'https://peeringdb.com/api/poc?net_id=%s' % netid
    api_data = requests.get(url, auth=(pdbusername, pdbpassword))

    returndata = []
    json_data = api_data.json()
    for x in json_data['data']:
	returndata.append(x['email'])
    return returndata
