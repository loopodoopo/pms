#!/usr/bin/python
#
# Hibernia Networks - Peering Management System - 2016
# Maikel de Boer - maikel.deboer@hibernianetworks.com

#Main project modules

import ncclient, ConfigParser, re, ipaddress, peeringdb, hashlib, time, os, json, sys, smtplib
from jinja2 import Environment, FileSystemLoader
from ncclient import manager
from xml.etree import ElementTree
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from smtplib import SMTP
#Project modules
import pdb

asndictcachetime = 86400
devicecachetime = 600

def parse_config():
    #get all the devices in the config.cfg file
    devices = []
    try:
        config = ConfigParser.ConfigParser()
        config.readfp(open('config.cfg'))
        for line in config.items('device'):
            devices.append(line)
    except:
        print 'Could not read config.cfg'

    return devices

def netconf(device, vendor, username, password):
    #Get current current configuration from device using netconf
    m = manager.connect(host=device,
                       username=username,
                       password=password,
                       timeout=300,
                       allow_agent=False,
                       hostkey_verify=False)

    if vendor == 'juniper':
        #To speed things up we only download 3 parts of the config
        routing_options = m.get_config(source='running', filter=('subtree', '<configuration><routing-options>')).data_xml
        protocols_bgp = m.get_config(source='running', filter=('subtree', '<configuration><protocols><bgp>')).data_xml
        interfaces = m.get_config(source='running', filter=('subtree', '<configuration><interfaces>')).data_xml
	#Removing header and tails because we already have one
	routing_options = '\n'.join(routing_options.split('\n')[2:-3])
	protocols_bgp = '\n'.join(protocols_bgp.split('\n')[2:-3])
	interfaces = '\n'.join(interfaces.split('\n')[2:-3])
	#Fixing the document to be kind of valid
        config = '<root>\n%s\n%s\n%s\n</root>' % (routing_options, protocols_bgp, interfaces)

    if vendor == 'cisco':
        print 'Vendor not supported. Could you please build this?'

    return config

def netconfedit(device, vendor, username, password, action, peergroup, peerasn, peerip, pfxlimit, md5):
    #We use this function to edit config on a device
    if vendor == 'juniper':
        m = manager.connect(host=device,
                       username=username,
                       password=password,
                       timeout=300,
                       allow_agent=False,
		       device_params={'name': 'junos'},
                       hostkey_verify=False)

	#Check the version of the peer we are trying to add
	checkblock = ipaddress.ip_address(unicode(peerip))

	#Collect all details to render the config template
	template_var = {}
	template_var['action'] = action
	template_var['version'] = str(checkblock.version)
	template_var['peergroup'] = peergroup
	template_var['peerasn'] = peerasn
	template_var['peerip'] = peerip
	template_var['pfxlimit'] = pfxlimit
	template_var['md5'] = md5

	#Get teardown statement from config.cfg
	try:
            configuration = ConfigParser.ConfigParser()
            configuration.readfp(open('config.cfg'))
            template_var['teardown'] = configuration.get('juniper', 'teardown')
	except:
	    print 'Notice: Juniper teardown not set in config. We will use 80 now'
	    template_var['teardown'] = "80"

	#Render the configuration from template
        returnconfig = create_config(vendor, template_var)
	print 'To deploy:\n%s' % returnconfig

        #Lock the device before configuring
        try:
 	    m.lock()
	except ncclient.operations.rpc.RPCError:
            return 'Somebody is in configure mode on the %s device - ABORTING' % device
            sys.exit(2)

        #Sending the config to the device and unlock once done
        print 'Sending to %s' % device
	send_config = m.load_configuration(action='set', config=returnconfig)
	check_config = m.validate()
        if 'error' in check_config.tostring:
	    print 'the configuration contains errors - manual investigation is needed - ABORTING'
	    m.unlock()
	    m.close_session()
	    sys.exit(2)

	m.commit()
	m.unlock()
	m.close_session()

        #We need to update the local cache.
        #we might want to add/remove/del 1 line instead of rebuilding everything in the future.
	print 'Updating cache...'
	try:
	    temp_dir = '/tmp/'
	    os.remove(temp_dir + hashlib.sha224(device + vendor).hexdigest() + '.cache.txt')
	    get_cached_asn_dict()
	    print 'Cache updated'
	except:
	    print 'No need to update'

    if vendor == 'cisco':
        print 'Vendor not supported. Could you please build this?'

def create_config(vendor, template_var):
    #Render the router config template with all the variables we collected
    template_dir = 'templates/router'
    template_name = '%s.tpl' % vendor
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)

    for line in template.render(template_var).splitlines():
        if not line.startswith('#') and len(line) > 0:
            try:
                config += '%s \n' % line
            except:
                config = '%s \n' % line

    return config

def get_cached_asn_dict():
    #Cache function for asndict. If we don't have a valid cache, we build one.
    temp_dir = '/tmp/'
    filename = '%sasndict.cache.txt' % temp_dir
    time_ago = time.time() - asndictcachetime

    if os.path.isfile(filename) and os.path.getctime(filename) > time_ago:
        with open(filename) as json_file:
            return json.load(json_file)
    else:
        data = pdb.build_asn_dict()
        json_data = json.dumps(data)
        handle = open(filename, "w")
        handle.write(json_data)
        handle.close
        return data

def get_cached_data_for_gui(devicename, vendor, username, password):
    #Cache function for gui data. If we don't have up to date cache, we will create one
    temp_dir = '/tmp/'
    filename = temp_dir + hashlib.sha224(devicename + vendor).hexdigest() + '.cache.txt'
    time_ago = time.time() - devicecachetime
    if os.path.isfile(filename) and os.path.getctime(filename) > time_ago:
    	with open(filename) as json_file:
	    return json.load(json_file)
    else:
	data = get_data_for_gui(devicename, vendor, username, password, get_cached_asn_dict())
    	json_data = json.dumps(data)
        handle = open(filename, "w")
    	handle.write(json_data)
        handle.close
    	return data

def get_data_for_gui(devicename, vendor, username, password, asndict):
    #Collect all data from the router and peeringdb to build the GUI.
    #We use a list of lists to collect the data. The format of the list and the position of the item is displayed in the comments below.
    #If you build a new vendor preserve the positions in the list of lists so you can render it in the GUI template correctly.
    #For Juniper it is important that local-address is configured on the IX peergroup.
    if vendor == 'juniper':
        return_data = []
        config = netconf(devicename, vendor, username, password)
        tree = ElementTree.fromstring(config)

        #0: devicename, vendor, username, password, asn, asname
        asn = tree.findtext('.//autonomous-system/as-number')
        try:
            asname = asndict[asn]
        except:
            asname = 'Unkown'
        return_data.append([devicename, vendor, username, password, asn, asname])

        #1: available peer-groups
        peergroups = tree.findall('.//bgp/group/name')
        peergroup_collection = []
        for group in peergroups:
            peergroup_collection.append(group.text)
        return_data.append(peergroup_collection)

        #2: IX (xid, ixname)
        localaddress = tree.findall('.//bgp/group/local-address')
        localaddress_collection = []
        for address in localaddress:
            cidr = re.findall(address.text + '\/\d*', config)
            if not cidr:
                localaddress_collection.append((0, 'No IX found'))
                return_data.append(localaddress_collection)
                return return_data
            if not cidr[0].endswith(('32', '128')):
                ixid = pdb.map_pfx_to_ix(cidr[0])
                name = pdb.map_id_to_ix(ixid)
                if (ixid, name) not in localaddress_collection:
                    localaddress_collection.append((ixid, name))
        return_data.append(localaddress_collection)

        #3: configured (ixid, asn, name, ip, peergroup, pfxlimit, md5)
        configured_collection = []
        peergroups = tree.findall('.//bgp/group')
        for x in peergroups:
            peergroup =  x.findtext('.//name')
            neighbors = x.findall('neighbor')
            for y in neighbors:
                if y.findtext('.//peer-as'):
                    peerasn = y.findtext('.//peer-as')
                    peercidr = y.findtext('.//name')
                    checkblock = ipaddress.ip_address(unicode(peercidr))
                    #find the max prefix limit
                    pfxlimit = 'Max PFX limit'
                    if checkblock.version is 4:
                        pfxlimit = x.findtext('.//family/inet/unicast/prefix-limit/maximum')
                        pfxlimitpeer = y.findtext('.//family/inet/unicast/prefix-limit/maximum')
                        if pfxlimitpeer:
                            pfxlimit = pfxlimitpeer
                    if checkblock.version is 6:
                        pfxlimit = x.findtext('.//family/inet6/unicast/prefix-limit/maximum')
                        pfxlimitpeer = y.findtext('.//family/inet6/unicast/prefix-limit/maximum')
                        if pfxlimitpeer:
                            pfxlimit = pfxlimitpeer
                    md5 = y.findtext('.//authentication-key')
                    if not md5:
                        md5 = ''
                    try:
                        asnname = asndict[peerasn]
                    except:
                        asnname = 'Unknown'
                    configured_collection.append(('', peerasn, asnname, peercidr, peergroup, pfxlimit, md5))
        #Sort the list so we don't have to when we render
        return_data.append(sorted(configured_collection, key=lambda nr: int(nr[1])))

        #4: not-configured (ixid, asn, name, ipv4, ipv6)
        not_configured_collection = []
        for ix in localaddress_collection:
            on_ix = pdb.get_asn_on_ix(ix[0])
            for row in on_ix:
                row.update({'checked_v4': 'false', 'checked_v6': 'false'})

            for item in on_ix:
                for x in configured_collection:
                    if x[3] == item['ipaddr4']:
                        item.update({'checked_v4': 'true'})
                    if x[3] == item['ipaddr6']:
                        item.update({'checked_v6': 'true'})

            for row in on_ix:
                if row['checked_v4'] is not 'true' and row['ipaddr4'] is not None:
                    try:
                        asname = asndict[str(row['asn'])]
                    except:
                        asname = 'Unknown'
                    not_configured_collection.append((row['ix_id'], row['asn'],asname, row['ipaddr4']))
                if row['checked_v6'] is not 'true' and row['ipaddr6'] is not None:
                    try:
                        asname = asndict[str(row['asn'])]
                    except:
                        asname = 'Unknown'
                    not_configured_collection.append((row['ix_id'], row['asn'],asname, row['ipaddr6']))

        #Again we sort the list
        return_data.append(sorted(not_configured_collection, key=lambda nr: int(nr[1])))

        return return_data

    if vendor == 'cisco':
        print 'Vendor not supported. Could you please build this?'

def sendmail(address, subject, message):
    #Sends out e-mails to posible peers using your localy configured smtp server.
    #We might want to make the mail server configurable.
    config = ConfigParser.ConfigParser()
    config.readfp(open('config.cfg'))

    fromaddr = config.get('mail', 'from')
    server = SMTP(config.get('mail', 'smtp'))
    toaddr = str(address).split()

    msg = MIMEText(message)
    sender = config.get('mail', 'from')
    msg['Subject'] = subject
    msg['From'] = fromaddr 
    msg['To'] = ", ".join(toaddr) 

    server.sendmail(fromaddr, toaddr, msg.as_string())
    server.quit()

def main():
    #This function does nothing. I use it to test individual parts of the code.
    print 'Running...\n'

#main()
