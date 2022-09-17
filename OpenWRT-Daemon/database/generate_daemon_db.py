import sqlite3
import os

possible_configs = ["ipv4","dhcp","dhcp_static","dhcp_relay","RIP","QoS","DNS","fw"]
ipv4_config = ["interface","ipaddr","netmask","gateway","dns"]
dhcp_config = ["interface","start","limit_dhcp","leasetime"]
dhcp_static_config = ["mac","ip"]
dhcp_relay_config = ["id_relay","interface","local_addr","server_addr"]
RIP_config = ["route_id","interface","target","netmask","gateway"]
QoS_config = ["interface","enabled","classgroup","overhead","download","upload"]
DNS_config = ["address"]
fw_config = ["name","src","src_ip","src_mac","src_port","proto","dest","dest_ip","dest_port","target"]

json_config = {"ipv4": ipv4_config,
               "dhcp":dhcp_config,
               "dhcp_static":dhcp_static_config,
               "dhcp_relay":dhcp_relay_config,
               "RIP":RIP_config,
               "QoS":QoS_config,
               "DNS":DNS_config,
               "fw":fw_config}

def create_host_db():
    conn = sqlite3.connect("./host_config.db")
    cursor = conn.cursor()
    cursor.execute("create table host (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, token TEXT, port INTEGER, netmask TEXT, address TEXT, auth INTEGER,token_status INTEGER);")
    cursor.execute("insert into host (token,port,netmask,address,auth,token_status) values (\"{}\",\"{}\",\"{}\",\"{}\",\"{}\",\"{}\")".format("Default",
                                                                                                               50000,
                                                                                                               "255.255.255.0",
                                                                                                               "127.0.0.1",
                                                                                                               0,
                                                                                                               0))
    conn.commit()
    conn.close()
    
def create_controller_db():
    conn = sqlite3.connect("./controller_config.db")
    cursor = conn.cursor()
    cursor.execute("create table controller (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, port INTEGER, netmask TEXT, address TEXT);")
    cursor.execute("insert into controller (port,netmask,address) values (\"{}\",\"{}\",\"{}\")".format(8081,
                                                                                                "255.255.255.0",
                                                                                                "127.0.0.1"))
    conn.commit()
    conn.close()
    
def create_config_db():
    conn = sqlite3.connect("./configs.db")
    cursor = conn.cursor()
    cursor.execute("create table ipv4 (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,who TEXT, interface TEXT, ipaddr TEXT, netmask TEXT, gateway TEXT, dns TEXT,logical_group TEXT, openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,interface TEXT, start INTEGER, limit_dhcp INTEGER, leasetime TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp_static (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,mac TEXT, ip TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp_relay (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,id_relay INTEGER, interface TEXT, local_addr TEXT, server_addr TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table RIP (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT, route_id TEXT, interface TEXT, target TEXT, netmask TEXT, gateway TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table QoS (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT, interface TEXT, enabled INTEGER, classgroup TEXT, overhead INTEGER, download INTEGER, upload INTEGER, logical_group TEXT, openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table DNS (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,address TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table fw (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,name TEXT, src TEXT, src_ip TEXT, src_mac TEXT, src_port INTEGER, proto TEXT, dest TEXT, dest_ip TEXT, dest_port TEXT, target TEXT, logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
        
    conn.commit()
    conn.close()

    
if __name__ == "__main__":
    os.system("rm ./*.db")
    create_host_db()
    create_config_db()
    create_controller_db()