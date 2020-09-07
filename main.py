# -*- coding: utf-8 -*-
#
# Autoconfigure network settings for your IOx app deployed on IR1101
# Flo Pachinger / flopach, Cisco Systems, Feb 2020
# Apache License 2.0
from ncclient import manager, xml_
from collections import OrderedDict
import xmltodict
import xml.dom.minidom
import json
from string import Template

def parse_json():
    global config
    try:
        jsonfile = open("data.json")
        jsonstr = jsonfile.read()
        config = json.loads(jsonstr)
        print("Parsed data.json")
    except:
        print("JSON parsing error - check if you have a valid JSON!")
        exit()

def connecting():
    global m
    try:
        m = manager.connect(host=config["IOS-XE"]["ip-address"], port=int(config["IOS-XE"]["port"]),username=config["IOS-XE"]["username"],password=config["IOS-XE"]["password"],hostkey_verify=False)
        print("Connected to IR1101")
    except:
        print("Connection Error - check your username, password and connection to the device!")
        exit()


# get the running config in XML of the device
def get_running_config():
    netconf_reply = m.get_config(source='running')
    netconf_data = xml.dom.minidom.parseString(netconf_reply.xml).toprettyxml()
    print(netconf_data)

def change_config(var):
    #Configuration to change in XML, insert variables from data.json
    config_change_str = '''
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <app-hosting-cfg-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-app-hosting-cfg">
			<apps>
				<app>
					<application-name>${IOX_appid}</application-name>
					<application-network-resource>
						<vnic-gateway-0>0</vnic-gateway-0>
						<virtualportgroup-guest-interface-name-1>0</virtualportgroup-guest-interface-name-1>
						<virtualportgroup-guest-ip-address-1>${IOX_ip_iox_app}</virtualportgroup-guest-ip-address-1>
						<virtualportgroup-guest-ip-netmask-1>${IOX_subnetmask}</virtualportgroup-guest-ip-netmask-1>
						<virtualportgroup-application-default-gateway-1>${IOX_ip_virtualportgroup0}</virtualportgroup-application-default-gateway-1>
						<virtualportgroup-guest-interface-default-gateway-1>0</virtualportgroup-guest-interface-default-gateway-1>
					</application-network-resource>
				</app>
			</apps>
		</app-hosting-cfg-data>
		<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
		    <ip>
			    <nat xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-nat">
					<inside>
						<source>
							<static>
							</static>
						</source>
					</inside>
				</nat>
			</ip>
		    <interface>
		        <VirtualPortGroup>
					<name>0</name>
					<ip>
						<address>
							<primary>
								<address>${IOX_ip_virtualportgroup0}</address>
								<mask>${IOX_subnetmask}</mask>
							</primary>
						</address>
						<virtual-reassembly/>
						<nat xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-nat">
							<inside/>
						</nat>
					</ip>
				</VirtualPortGroup>
				<Vlan>
					<name>${OUTSIDE_INTERFACE_vlan_id}</name>
					<ip>
						<address>
							<primary>
								<address>${OUTSIDE_INTERFACE_ip_address}</address>
								<mask>${OUTSIDE_INTERFACE_subnetmask}</mask>
							</primary>
						</address>
						<virtual-reassembly/>
						<nat xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-nat">
							<outside/>
						</nat>
					</ip>
				</Vlan>
				<GigabitEthernet>
					<name>0/0/0</name>
					<media-type>rj45</media-type>
					<ip>
					    <address>
							<primary>
								<address>${OUTSIDE_INTERFACE_ip_address}</address>
								<mask>${OUTSIDE_INTERFACE_subnetmask}</mask>
							</primary>
						</address>
						<virtual-reassembly/>
						<nat xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-nat">
							<outside/>
						</nat>
					</ip>
				</GigabitEthernet>
			</interface>
		</native>
		</config>'''
    config_change_str = Template(config_change_str).substitute(IOX_appid = config["IOX"]["appid"],
    IOX_ip_iox_app = config["IOX"]["ip-iox-app"],
    IOX_ip_virtualportgroup0 = config["IOX"]["ip-virtualportgroup0"],
    IOX_subnetmask = config["IOX"]["subnetmask"],
    OUTSIDE_INTERFACE_vlan_id = config["OUTSIDE-INTERFACE"]["vlan-id"],
    OUTSIDE_INTERFACE_ip_address = config["OUTSIDE-INTERFACE"]["ip-address"],
    OUTSIDE_INTERFACE_subnetmask = config["OUTSIDE-INTERFACE"]["subnetmask"])
    config_change = xmltodict.parse(config_change_str)

    #What global interface should be used? Remove the configuration from the other interface
    # Tell for NAT configuration which interface it is and add it to the ordered dictionary config_change
    if var == 1:
        interface = OrderedDict([("GigabitEthernet", "0/0/0")])
        del config_change["config"]["native"]["interface"]["Vlan"]
    elif var == 2:
        interface = OrderedDict([("Vlan", config["OUTSIDE-INTERFACE"]["vlan-id"])])
        del config_change["config"]["native"]["interface"]["GigabitEthernet"]
    else:
        exit("Wrong User Input!")

    # iterating through the pre-defined port mappings in data.json
    # adding ordered lists to the config dictionary - later on it will be converted to XML via xml2dict library
    portmapping_od = OrderedDict()
    portmapping_od["nat-static-proto-transport-interface-list"] = []

    #protocol : local-port : global-port
    for portmapping in config["IOX"]["port-mapping"]:
        portmappings = portmapping.split(":")
        portmapping_od_item = OrderedDict([("proto",portmappings[0]),("local-ip",config["IOX"]["ip-iox-app"]),("local-port",portmappings[1]),("interface",interface),("global-port",portmappings[2])])
        portmapping_od["nat-static-proto-transport-interface-list"].append(portmapping_od_item)
    config_change["config"]["native"]["ip"]["nat"]["inside"]["source"]["static"] = portmapping_od

    #DICT --> XML
    config_change_str = xmltodict.unparse(config_change)
    #command for troubleshooting - gets you the config which will be sent
    #print(xml.dom.minidom.parseString(config_change_str).toprettyxml())
    netconf_reply = m.edit_config(target='running', config=config_change_str)
    print("Did it work? {}".format(netconf_reply.ok))

def save_running_config():
    rpc_body = '''<cisco-ia:save-config xmlns:cisco-ia="http://cisco.com/yang/cisco-ia"/>'''
    netconf_reply = m.dispatch(xml_.to_ele(rpc_body))
    print("Did it work? {}".format(netconf_reply.ok))

if __name__ == "__main__":
    print("""Hi! Here you can autoconfigure the network settings for your IOx App on the IR1101!
Please check if "netconf-yang" is enabled on the IR1101!

Please insert your configuration into data.json:
- IOS XE: Insert the IP address of the IR1101 and your IOS username and password

- IOX: Put the name of your installed application, ip addresses (leave default if unsure) and the open ports.
    <udp or tcp> : <Port of IOx App> : <Port reachable outside of IOx> (can be the same port)
    You may create more entries!
     
- Outside-Interface: The IP address of the device in the outside network (probably same IP address as under IOS XE).
    Please select now which interface you want to use:
    1: GigabitEthernet0/0/0
    2: VLAN as set in data.json
    
    OR: 3: Show running configuration\n""")
    var = int(input("Select: "))
    print("Starting...")
    parse_json()
    connecting()
    if var == 1 or var == 2:
        print("Changing configuration...")
        change_config(var)
        print("Saving configuration...")
        save_running_config()
    elif var == 3:
        get_running_config()
    else:
        print("Wrong input - please write only one number according to its action.")