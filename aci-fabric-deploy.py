#!/bin/python
################################################################################
#        _____     _          _           ____             _                   #
#       |  ___|_ _| |__  _ __(_) ___     |  _ \  ___ _ __ | | ___  _   _       #
#       | |_ / _` | '_ \| '__| |/ __|____| | | |/ _ \ '_ \| |/ _ \| | | |      #
#       |  _| (_| | |_) | |  | | (_|_____| |_| |  __/ |_) | | (_) | |_| |      #
#       |_|  \__,_|_.__/|_|  |_|\___|    |____/ \___| .__/|_|\___/ \__, |      #
#                                                   |_|            |___/       #
#                                                                              #
#        == A tool to deploy physical configuration on an ACI fabric ==        #
#                                                                              #
################################################################################
#                                                                              #
# [+] Written by:                                                              #
#  |_ Luis Martin (lumarti2@cisco.com)                                         #
#  |_ CITT Software CoE.                                                       #
#  |_ Cisco Advanced Services, EMEAR.                                          #
#                                                                              #
################################################################################
#                                                                              #
# Copyright (c) 2015-2016 Cisco Systems                                        #
# All Rights Reserved.                                                         #
#                                                                              #
#    Unless required by applicable law or agreed to in writing, this software  #
#    is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF   #
#    ANY KIND, either express or implied.                                      #
#                                                                              #
################################################################################

# Standard Imports
import sys
import json

# External library imports:
# 1. Fabriclib: a companion lib that encapsulates all low-level complexity
from acifabriclib import Fabric, VPC, InterfacePolicies, AccessPort, PortChannel

# 2. ACItoolkit is only used for its command-line parsing capabilities. 
# @todo: replace this at some point to eliminate the dependancy
from acitoolkit.acitoolkit import Session, Credentials

# Internal imports
from tools import *

# FUNCTIONS
def print_banner():
    output("                                                                   ")
    output("   _____     _          _           ____             _             ")
    output("  |  ___|_ _| |__  _ __(_) ___     |  _ \  ___ _ __ | | ___  _   _ ")
    output("  | |_ / _` | '_ \| '__| |/ __|____| | | |/ _ \ '_ \| |/ _ \| | | |")
    output("  |  _| (_| | |_) | |  | | (_|_____| |_| |  __/ |_) | | (_) | |_| |")
    output("  |_|  \__,_|_.__/|_|  |_|\___|    |____/ \___| .__/|_|\___/ \__, |")
    output("                                              |_|            |___/ ")
    output("                                                                   ")
    output("  == A tool to deploy physical configuration on an ACI fabric ==   \n")

# Start of the execution
if __name__ == "__main__":
    
    # Argument parsing. We use the ACI toolkit logic here, which tries to
    # retrieve credentials from the following places:
    # 1. Command line options
    # 2. Configuration file called credentials.py
    # 3. Environment variables
    # 4. Interactively querying the user
    # At the end, we should have an object args with all the necessary info.
    description = 'APIC credentials'
    creds = Credentials('apic', description)
    creds.add_argument('-i', "--input", default=None, help='Input file')
    creds.add_argument('-d', "--debug", default=None, help='Input file')
    args = creds.get()
    
    # Let's check if the user passed all relevant parameters
    if args.input is None:
        fatal("[E] Input filename missing. Please pass it using --input <filename>")
    if args.debug is not None:
        debug_enable()

    # First of all, parse the input file.
    data = parse_spreadsheet(args.input)
    
    interfaces = [] # List of interfaces to push to the fabric
    
    for config_line in data['PortMapping']:        

        # Parse destination interface(s)
        ports=[]
        nodes={}
        for p in ["leaf-port-1", "leaf-port-2", "leaf-port-3", "leaf-port-4"]:
            port_info = config_line[p]
            if port_info not in [None, "", "n/a", "N/A"]:
                try:
                    leaf, card, port = port_info.split("/")
                except:
                    fatal("[E] Incorrect port specification (%s) for interface %s." % (port_info, config_line['iface-name']))
                nodes[leaf]=True
                ports.append( {'leaf':leaf, 'card':card, 'port':port } )

        # Here we decide if we have to create an access port, a PortChannel or a VPC
        # and instance the appropriate type of object
        if len(nodes)==1:
            # One node, one interface -> access port
            if len(ports)==1:
                iface = AccessPort(config_line['iface-name'])
            # One node, multiple ports -> port channel
            else:
                iface = PortChannel(config_line['iface-name'])
        elif len(nodes)==2:
            # More than one node -> VPC
            iface = VPC(config_line['iface-name'])
        else:
           fatal("[E] Incorrect number of leaf nodes in interface specification (interface %s)." % config_line['iface-name'])

        # Set up port(s)
        for i in ports:
            iface.add_port(i['leaf'], i['card'], i['port'])
        
        
        # Set up Attachable Access Entity Propfile
        iface.associate_aep(config_line['aep'])
        
        # CDP Policy
        if config_line['iface-cdp'].lower() in ["enabled", "enable", "y", "yes"]:
            iface.cdp_enabled()
        elif config_line['iface-cdp'].lower() in ["disabled", "disable", "n", "no"]:
            iface.cdp_disabled()
        elif config_line['iface-cdp'].lower() != "default":
            warning("[W] Unexpected CDP policy (%s) on interface %s. Setting to 'default'" % (config_line['iface-cdp'], config_line['iface-name']))
        
        # LLDP Policy
        if config_line['iface-lldp'].lower() in ["enabled", "enable", "y", "yes"]:
            iface.lldp_enabled()
        elif config_line['iface-lldp'].lower() in ["disabled", "disable", "n", "no"]:
            iface.lldp_disabled()
        elif config_line['iface-lldp'].lower() != "default":
            warning("[W] Unexpected LLDP policy (%s) on interface %s. Setting to 'default'" % (config_line['iface-lldp'], config_line['iface-name']))

        # LACP Policy
        if config_line['iface-lacp'].lower() == "active":
            iface.lacp_active()
        elif config_line['iface-lacp'].lower() == "passive":
            iface.lacp_passive()
        elif config_line['iface-lacp'].lower() == "off":
            iface.lacp_off()
        elif config_line['iface-lacp'].lower() != "default":
            warning("[W] Unexpected LACP policy (%s) on interface %s. Setting to 'default'" % (config_line['iface-lacp'], config_line['iface-name']))

        # MCP Policy
        if config_line['iface-mcp'].lower() in ["enabled", "enable", "y", "yes"]:
            iface.mcp_enabled()
        elif config_line['iface-mcp'].lower() in ["disabled", "disable", "n", "no"]:
            iface.mcp_disabled()
        elif config_line['iface-mcp'].lower() != "default":
            warning("[W] Unexpected MCP policy (%s) on interface %s. Setting to 'default'" % (config_line['iface-mcp'], config_line['iface-name']))
        
        # Link Policy
        if config_line['speed-auto'].lower() in ["y", "yes", "auto", "dynamic", "negotiate"]:
            iface.link(config_line['iface-speed'], True)
        elif config_line['speed-auto'].lower() in ["n", "no", "manual", "static", "nonegotiate"]:
            iface.link(config_line['iface-speed'], False)
        else:
            warning("[W] Unexpected Link Speed negotation policy (%s) on interface %s. Setting to 'default'" % (config_line['speed-auto'], config_line['iface-name']))
        
        # STP Policy
        if config_line['iface-bpdu-guard'].lower() in ["enabled", "enable", "y", "yes"]:
            iface.stp_bpdu_guard()
        if config_line['iface-bpdu-filter'].lower() in ["enabled", "enable", "y", "yes"]:
            iface.stp_bpdu_filter()
       
        # We are done with this interface. Add it to the list so we can push it 
        # to the fabric later
        interfaces.append(iface)
       
    # Now, we log into the APIC
    fabric = Fabric(args.url, args.login, args.password)
    fabric.connect()
    
    # First, deploy basic interface policies (CDP_Enabled, LACP_Active, etc)
    ifpols = InterfacePolicies()
    print_banner()
    output("[+] Creating standard interface policies")
    fabric.push_to_apic(ifpols)
    
    # Now push every interface we created earlier
    for iface in interfaces:
        output("[+] Creating interface '%s'" % iface.name)
        fabric.push_to_apic(iface)

    sys.exit(0)
