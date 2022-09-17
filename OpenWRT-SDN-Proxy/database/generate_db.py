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
    conn = sqlite3.connect("./hosts_groups.db")
    cursor = conn.cursor()
    cursor.execute("create table openwrt (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, address TEXT, port INTEGER, netmask TEXT, group_name TEXT, token TEXT);")
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
    cursor.execute("create table ipv4 (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,who TEXT, interface TEXT, ipaddr TEXT, netmask TEXT, gateway TEXT, dns TEXT,logical_group TEXT, openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,interface TEXT, start INTEGER, limit_dhcp INTEGER, leasetime TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp_static (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,mac TEXT, ip TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table dhcp_relay (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,id_relay INTEGER, interface TEXT, local_addr TEXT, server_addr TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table RIP (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,interface TEXT, target TEXT, netmask TEXT, gateway TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table QoS (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT, route_id TEXT, interface TEXT, enabled INTEGER, classgroup TEXT, overhead INTEGER, download INTEGER, upload INTEGER, logical_group TEXT, openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table DNS (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,address TEXT,logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
    cursor.execute("create table fw (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, who TEXT,name TEXT, src TEXT, src_ip TEXT, src_mac TEXT, src_port INTEGER, proto TEXT, dest TEXT, dest_ip TEXT, dest_port TEXT, target TEXT, logical_group TEXT,openwrt_ipv4 TEXT, rule_hash TEXT, enable INTEGER, minute INTEGER, month INTEGER, dayofweek INTEGER, hour INTEGER, dayofmonth INTEGER);")
        
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
    
def create_controller_db():
    conn = sqlite3.connect("./controller.db")
    cursor = conn.cursor()         
    # Cria tabela que vai armazenar a configuração da northboundAPI
    cursor.execute("create table northboundAPI (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, port INTEGER, address TEXT, token TEXT);")
    # Cria tabela que vai armazenar a configuração da southboundPAI
    cursor.execute("create table southboundAPI (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, port INTEGER, address TEXT);")
    # Cria tabela que vai armazenar a configuração do socket da southboundAPI
    cursor.execute("create table southbound_socket (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, port INTEGER, address TEXT);")
    # Cria tabela que vai armazenar a configuração do db_daemon
    cursor.execute("create table db (id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, port INTEGER, address TEXT);")
    
    # Insere os valores padrões em cada uma das configurações
    cursor.execute("insert into northboundAPI (port,address,token) values (\"{}\",\"{}\",\"{}\")".format(8080,
                                                                                            "127.0.0.1",
                                                                                            "0"))
    cursor.execute("insert into southboundAPI (port,address) values (\"{}\",\"{}\")".format(8081,
                                                                                            "127.0.0.1"))
    cursor.execute("insert into southbound_socket (port,address) values (\"{}\",\"{}\")".format(65002,
                                                                                            "127.0.0.1"))
    cursor.execute("insert into db (port,address) values (\"{}\",\"{}\")".format(65001,
                                                                                "127.0.0.1"))
    
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    os.system("rm ./*.db")
    create_config_db()
    create_config_parameters_db()
    create_host_db()
    create_group_db()
    create_controller_db()