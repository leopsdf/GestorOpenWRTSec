import sqlite3
import os

possible_configs = ["ipv4","dhcp","dhcp_static","dhcp_relay","RIP","QoS","DNS","fw"]
ipv4_config = ["ipaddr","netmask","gateway","dns"]
dhcp_config = ["interface","start","limit_dhcp","leasetime"]
dhcp_static_config = ["mac","ip"]
dhcp_relay_config = ["id_relay","interface","local_addr","server_addr"]
RIP_config = ["interface","target","netmask","gateway"]
QoS_config = ["interface","enabled","classgroup","overhead","download","upload"]
DNS_config = ["address"]
fw_config = ["placeholder"]

json_config = {"ipv4": ipv4_config,
               "dhcp":dhcp_config,
               "dhcp_static":dhcp_static_config,
               "dhcp_relay":dhcp_relay_config,
               "RIP":RIP_config,
               "QoS":QoS_config,
               "DNS":DNS_config,
               "fw":fw_config}

def create_host_db():
    conn = sqlite3.connect("./hosts_groups.db")
    cursor = conn.cursor()
    cursor.execute("create table openwrt (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, address TEXT, port INTEGER, netmask TEXT, group_name TEXT);")
    conn.commit()
    conn.close()
    
def create_group_db():
    conn = sqlite3.connect("./hosts_groups.db")
    cursor = conn.cursor()
    cursor.execute("create table groups (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, group_name TEXT);")
    cursor.execute("insert into groups (group_name) values (\"{}\");".format("Default"))
    conn.commit()
    conn.close()
    
def create_config_db():
    conn = sqlite3.connect("./configs.db")
    cursor = conn.cursor()
    cursor.execute("create table ipv4 (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,who TEXT, ipaddr TEXT, netmask TEXT, gateway TEXT, dns TEXT,logical_group TEXT, openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,interface TEXT, start INTEGER, limit_dhcp INTEGER, leasetime TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp_static (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,mac TEXT, ip TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp_relay (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,id_relay INTEGER, interface TEXT, local_addr TEXT, server_addr TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table RIP (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,interface TEXT, target TEXT, netmask TEXT, gateway TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table QoS (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,interface TEXT, enabled INTEGER, classgroup TEXT, overhead INTEGER, download INTEGER, upload INTEGER,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table DNS (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,address TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table fw (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,placeholder TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    
    conn.commit()
    conn.close()
    
def create_config_parameters_db():
    conn = sqlite3.connect("./configs_parameters.db")
    cursor = conn.cursor()
    for config_type in possible_configs:
        cursor.execute("create table \"{}\" (config_name TEXT);".format(config_type))
        for config_name in json_config[config_type]:
            cursor.execute("insert into \"{}\" (config_name) values (\"{}\");".format(config_type,config_name))
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    os.system("rm ./*.db")
    create_config_db()
    create_config_parameters_db()
    create_host_db()
    create_group_db()