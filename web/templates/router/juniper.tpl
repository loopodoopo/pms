# Hibernia Networks - Peering Management System - 2016
# Maikel de Boer - maikel.deboer@hibernianetworks.com

#Juniper MX series config template.

#Adding
#v4
{% if action == "add" %}
{% if version == "4" %}
set protocols bgp group {{ peergroup }} neighbor {{ peerip }} peer-as {{ peerasn }} {% if md5 %} authentication-key {{ md5 }} {% endif %} {% if pfxlimit %} family inet unicast prefix-limit maximum {{ pfxlimit }} teardown {{ teardown }} {% endif %}
{% endif %}

#v6
{% if version == "6" %}
set protocols bgp group {{ peergroup }} neighbor {{ peerip }} peer-as {{ peerasn }} {% if md5 %} authentication-key {{ md5 }} {% endif %} {% if pfxlimit %} family inet6 unicast prefix-limit maximum {{ pfxlimit }} teardown {{ teardown }} {% endif %}
{% endif %}
{% endif %}

#Update
#v4
{% if action == "update" %}
{% if version == "4" %}
del protocols bgp group {{ peergroup }} neighbor {{ peerip }}
set protocols bgp group {{ peergroup }} neighbor {{ peerip }} peer-as {{ peerasn }} {% if md5 %} authentication-key {{ md5 }} {% endif %} {% if pfxlimit %} family inet4 unicast prefix-limit maximum {{ pfxlimit }} teardown {{ teardown }}{% endif %}
{% endif %}

#v6
{% if version == "6" %}
del protocols bgp group {{ peergroup }} neighbor {{ peerip }}
set protocols bgp group {{ peergroup }} neighbor {{ peerip }} peer-as {{ peerasn }} {% if md5 %} authentication-key {{ md5 }} {% endif %} {% if pfxlimit %} family inet6 unicast prefix-limit maximum {{ pfxlimit }} teardown {{ teardown }}{% endif %}
{% endif %}
{% endif %}

#Deleting
{% if action == "del" %}
del protocols bgp group {{ peergroup }} neighbor {{ peerip }}
{% endif %}
