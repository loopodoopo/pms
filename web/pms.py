# Hibernia Networks - Peering Management System - 2016
# Maikel de Boer - maikel.deboer@hibernianetworks.com

from flask import Flask, render_template, request
from modules import main, pdb

app = Flask(__name__)
app.config.update(
    DEBUG=True,
    TEMPLATES_AUTO_RELOAD=True
)


#Flask menu structure functions
@app.route('/', methods=['GET'])
def render_home():
    devices = main.parse_config()
    return render_template('index.html', devices=devices)

@app.route('/router', methods=['GET'])
def render_router():
    devicename = request.args.get('device', '')
    if devicename is not '':
	devices = main.parse_config()
	for device in devices:
   	    if device[0] == devicename:
		vendor = device[1].split(', ')[0]
		username = device[1].split(', ')[1]
		password = device[1].split(', ')[2]
		router_data = main.get_cached_data_for_gui(devicename, vendor, username, password)

		return render_template('index.html', devices=devices, device=devicename, \
		       ixes=router_data[2], asn=router_data[0][4], name=router_data[0][5])

	return "Unknown router: %s !" % devicename

    return 'No devicename given'

@app.route('/ixdetails', methods=['GET'])
def render_ixdetails():
    devicename = request.args.get('device', '')
    if devicename is not '':
        devices = main.parse_config()
	for device in devices:
          if device[0] == devicename:
	    vendor = device[1].split(', ')[0]
            username = device[1].split(', ')[1]
  	    password = device[1].split(', ')[2]
	    ix = request.args.get('ixname', '')
 	    router_data = main.get_cached_data_for_gui(devicename, vendor, username, password)

	    return render_template('index.html', devices=devices, device=devicename, \
						 ixes=router_data[2], ix=ix, asn=router_data[0][4], \
						 name=router_data[0][5])

@app.route('/ixdetails/configured', methods=['GET'])
def render_ixdetails_configured():
    devicename = request.args.get('device', '')
    if devicename is not '':
      devices = main.parse_config()
      for device in devices:
        if device[0] == devicename:
          vendor = device[1].split(', ')[0]
          username = device[1].split(', ')[1]
          password = device[1].split(', ')[2]
          ix = request.args.get('ixname', '')
          router_data = main.get_cached_data_for_gui(devicename, vendor, username, password)

	  return render_template('index.html', devices=devices, device=devicename, \
					       ixes=router_data[2], ix=ix, status='Configured', \
					       asn=router_data[0][4], name=router_data[0][5], \
				               data=router_data[3])

@app.route('/ixdetails/notconfigured', methods=['GET'])
def render_ixdetails_not_configured():
    devicename = request.args.get('device', '')
    if devicename is not '':
      devices = main.parse_config()
      for device in devices:
        if device[0] == devicename:
          vendor = device[1].split(', ')[0]
          username = device[1].split(', ')[1]
          password = device[1].split(', ')[2]
          ix = request.args.get('ixname', '')
	  router_data = main.get_cached_data_for_gui(devicename, vendor, username, password)

          return render_template('index.html', devices=devices, device=devicename, \
                                               ixes=router_data[2], ix=ix, status='Not Configured', \
                                               asn=router_data[0][4], name=router_data[0][5], \
                                               data=router_data[4], peergroups=router_data[1])

@app.route('/delete', methods=['GET'])
def render_delete():
    devicename = request.args.get('device', '')
    peername = request.args.get('peername', '')
    peerasn = request.args.get('peerasn', '')
    peerip = request.args.get('peerip', '')
    peergroup = request.args.get('peergroup', '')
    ix = request.args.get('ixname', '')
    pfxlimit = 0
    md5 = ''

    devices = main.parse_config()
    for device in devices:
        if device[0] == devicename:
	    vendor = device[1].split(', ')[0]
            username = device[1].split(', ')[1]
            password = device[1].split(', ')[2]

    #try:
    main.netconfedit(devicename, vendor, username, password, 'del', peergroup, peerasn, peerip, pfxlimit, md5)
    return render_template('deleted.html', peername=peername, peerasn=peerasn, peerip=peerip, ix=ix)
    #except:
#	return 'Error delting peer'

@app.route('/configure', methods=['GET'])
def render_configure():
    devices = main.parse_config()
    peername = request.args.get('peername', '')
    peerasn = request.args.get('peerasn', '')
    peerip = request.args.get('peerip', '')
    peergroup = request.args.get('peergroup', '')
    devicename = request.args.get('device', '')
    ix = request.args.get('ixname', '')
    pfxlimit = request.args.get('pfxlimit', '')
    md5 = request.args.get('md5', '')

    if devicename is not '':
      for device in devices:
        if device[0] == devicename:
          vendor = device[1].split(', ')[0]
          username = device[1].split(', ')[1]
          password = device[1].split(', ')[2]

    #try:
    main.netconfedit(devicename, vendor, username, password, 'add', peergroup, peerasn, peerip, pfxlimit, md5)
    return render_template('configured.html', peername=peername, peerasn=peerasn, peerip=peerip, ix=ix, peergroup=peergroup, pfxlimit=pfxlimit, md5=md5)
    #except:
#	return 'something went wrong configuring the peer'

@app.route('/update', methods=['GET'])
def render_update_peer():
    devices = main.parse_config()
    peername = request.args.get('peername', '')
    peerasn = request.args.get('peerasn', '')
    peerip = request.args.get('peerip', '')
    peergroup = request.args.get('peergroup', '')
    devicename = request.args.get('device', '')
    ix = request.args.get('ixname', '')
    pfxlimit = request.args.get('pfxlimit', '')
    md5 = request.args.get('md5', '')

    if devicename is not '':
      for device in devices:
        if device[0] == devicename:
          vendor = device[1].split(', ')[0]
          username = device[1].split(', ')[1]
          password = device[1].split(', ')[2]

    #try:
    main.netconfedit(devicename, vendor, username, password, 'update', peergroup, peerasn, peerip, pfxlimit, md5)
    return render_template('updated.html', peername=peername, peerasn=peerasn, peerip=peerip, ix=ix, peergroup=peergroup, pfxlimit=pfxlimit, md5=md5)
    #except:
#       return 'something went wrong updating the peer'

@app.route('/contactpeer')
def render_contactpeer():
    localname = request.args.get('localname', '')
    localasn = request.args.get('localasn', '')
    ix = request.args.get('ix', '')
    peername = request.args.get('peername', '')
    peerasn = request.args.get('peerasn', '')
    peerip = request.args.get('peerip', '')
    localasn = request.args.get('asn', '')
    mail = pdb.get_asn_contact(peerasn)

    return render_template('contactpeer.html', peername=peername, peerasn=peerasn, peerip=peerip, localasn=localasn, localname=localname, ix=ix, mail=mail)

@app.route('/mail', methods=['POST'])
def render_mail_send():
    address = request.form['MailAddress']
    subject = request.form['MailSubject']
    message = request.form['MailMessage']
    asn = request.form['asn']
    name = request.form['name']
	
    main.sendmail(address, subject, message)

    return render_template('mailsend.html', peername=name, asn=asn, address=address, subject=subject, message=message)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
