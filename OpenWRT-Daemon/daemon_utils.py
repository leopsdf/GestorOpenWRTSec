import os
import sqlite3
import pathlib
import json

FIREWALL_FILE = "/etc/config/firewall"
#FIREWALL_FILE = "./firewall"

# Coleta as informações do daemon
def startup_process():
    
    # Pega a porta do dispositivo gerenciado
    conn = sqlite3.connect("database/host_config.db")
    cursor = conn.cursor()
    # Atualiza o registro do host
    cursor.execute("select * from host where id = 1;")
    result = cursor.fetchall()
    
    # Dicionários das configs
    startup_config = {"token":result[0][1],
                      "port":int(result[0][2]),
                      "netmask":result[0][3],
                      "address":result[0][4],
                      "auth":int(result[0][5]),
                      "token_status":int(result[0][6])}
    
    conn.close()
    
    return startup_config

# Coleta as informações da controller
def controller_config():
    
    # Pega a porta do dispositivo gerenciado
    conn = sqlite3.connect("database/controller_config.db")
    cursor = conn.cursor()
    # Atualiza o registro do host
    cursor.execute("select * from controller where id = 1;")
    result = cursor.fetchall()
    
    # Dicionários das configs
    controller_config = {"port":int(result[0][1]),
                      "netmask":result[0][2],
                      "address":result[0][3]}
    
    conn.close()
    pass
    return controller_config

# Função que executa queries recebidas (SOMENTE INSERT)
def apply(query):
        
    conn = sqlite3.connect("database/configs.db")
    cursor = conn.cursor()
        
    # Executa todas as queries recebidas
    cursor.execute(query)

    # Salva as mudanças feitas
    conn.commit()
    conn.close()

# Método utilizado para a criação das queries utilizadas para salvar a regra no banco para cada entidade (cada IP)    
# Retorna um array com queries a serem aplicadas
def create_query_config(rule):
        
    # Nome da tabela definida pelo tipo da configuração
    table_name = rule["type"]
    # Define a primeira e segunda parte da query com os campos que não variam
    fist_part_query = "insert into {} (enable,minute,hour,dayofmonth,month,dayofweek,rule_hash".format(table_name)
    second_part_query = " values ({},{},{},{},{},{},\"{}\"".format(rule["schedule"]["enable"],
                                                                            rule["schedule"]["minute"],
                                                                            rule["schedule"]["hour"],
                                                                            rule["schedule"]["dayofmonth"],
                                                                            rule["schedule"]["month"],
                                                                            rule["schedule"]["dayofweek"],
                                                                            rule["rule_hash"])
    # Loop para inserção dos fields e seus valores na query da regra
    for field_name in rule["fields"].keys():
        fist_part_query += ",{}".format(field_name)
        second_part_query += ",\"{}\"".format(str(rule["fields"][field_name]))
            
    # Array que armazenará as queries criadas para cada entidade (regras separadas por ip's específicos)
    queries_array = []
    # Pega os nome dos grupos lógicos abordados na regra
    fist_part_query += ",openwrt_ipv4"
    second_part_query += ",\"{}\"".format(rule["targets"])
    fist_part_query += ")"
    second_part_query += ");"
    
    final_query = fist_part_query+second_part_query
    
    return final_query

# Apply firewall config on firewalld
def apply_firewall_config(payload,rule_hash):
    
    # Dicionário com o texto associado a configuração de todos os parâmetros suportados
    firewall_config = {"header":"config rule",
                    "name":"\toption name\t",
                   "src":"\toption src\t",
                   "src_ip":"\toption src_ip\t",
                   "src_mac":"\toption src_mac\t",
                   "src_port":"\toption src_port\t",
                   "dest":"\toption dest\t",
                   "dest_ip":"\toption dest_ip\t",
                   "dest_port":"\toption dest_port\t",
                   "proto":"\toption proto\t",
                   "target":"\toption target\t"}
    
    # Coloca o identificados da configuração no arquivo
    os.system("echo '\n#{}' >> {}".format(rule_hash,FIREWALL_FILE))
    # Coloca o cabeçalho da regra
    os.system("echo '{}' >> {}".format(firewall_config["header"],FIREWALL_FILE))
    
    configs = payload.keys()
    
    # Loop para inserção dos parâmetros da regras a partir do que foi enviado
    for config in configs:
        try:
            # Insere as configurações no arquivo do firewall
            os.system("echo '{}\t{}' >> {}".format(firewall_config[config],payload[config],FIREWALL_FILE))
                
        except KeyError:
            pass
    
    # Reinicializa o serviço
    os.system("/etc/init.d/firewall restart")            

# Remove configuração do arquivo
def delete_config(rule_hash, rule_type,config_dict):
    
    # Conecta ao banco de dados de configurações
    conn = sqlite3.connect("database/configs.db")
    cursor = conn.cursor()
    
    
    if rule_type == "fw":

        # Pega os parâmetros associados a configuração a ser deletada
        cursor.execute("select * from {} where rule_hash = '{}';".format(rule_type,rule_hash))
        result = cursor.fetchall()
        
        result_list = list(result[0])
        # Remove todos os Nones no resultado do banco
        result_list = [x for x in result_list if x is not None]
        
        new_result = []
        iterator = 0
        # Remove os últimos 6 elementos associados ao schedule
        while iterator < len(result_list)-6:
            new_result.append(result_list[iterator])
            iterator +=1
    
    
        # Pega a quantidade de parâmetros da configuração, -1 para remover o hash e o ID
        remove_size = len(new_result)-2
        
        #Remove a configuração do arquivo baseado no hash e em N (número de parâmetros) linhas em seguida
        os.system("sed -e '/{}/,+{}d' -i {}".format(rule_hash,remove_size,FIREWALL_FILE))
        
        os.system("/etc/init.d/firewall restart")
    
    # Remove a configuração de DNS
    elif rule_type == "DNS":
        # Remove a configuração do DNS a partir do hash
        os.system("sed -e '/{}/,+1d' -i /etc/resolv.conf".format(config_dict["rule_hash"]))
        
    # Remove a configuração de ipv4
    elif rule_type == "ipv4":
        os.system("uci delete network.{}.ipaddr='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["address"]))
        os.system("uci delete network.{}.netmask='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["netmask"]))
        os.system("uci delete network.{}.gateway='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["gateway"]))
        os.system("uci delete network.{}.dns='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["dns"]))
        
        os.system("uci commit network")
        os.system("/etc/init.d/network restart")
        
    # Remove a configuração de dhcp
    elif rule_type == "dhcp":
        os.system("uci delete dhcp.{}.interface='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["interface"]))
        os.system("uci delete dhcp.{}.start='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["start"]))
        os.system("uci delete dhcp.{}.limit='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["limit_dhcp"]))
        os.system("uci delete dhcp.{}.leasetime='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["leasetime"]))
        
        os.system("uci commit dhcp")
        os.system("/etc/init.d/odhcpd restart")
        
    # Remove a configuração de QoS
    elif rule_type == "QoS":
        # Remove a configuração do QoS a partir do hash
        os.system("sed -e '/{}/,+6d' -i /etc/config/qos".format(config_dict["rule_hash"]))
        os.system("/etc/init.d/qos restart")
    
    # Remove a configuração de RIP
    elif rule_type == "RIP":
        # Remove a configuração do RIP a partir do hash
        os.system("sed -e '/{}/,+5d' -i /etc/config/network".format(config_dict["rule_hash"]))
        os.system("/etc/inid.d/network restart")
        
    # Remove a configuração de dhcp_relay
    elif rule_type == "dhcp_relay":
        # Remove a configuração do dhcp_relay a partir do hash
        os.system("sed -e '/{}/,+4d' -i /etc/config/dhcp".format(config_dict["rule_hash"]))
        os.system("/etc/init.d/odhcpd restart")    
    
    # Remove a regra da base de dados 
    cursor.execute("delete from {} where rule_hash = '{}';".format(rule_type,rule_hash))
    
    conn.commit()
    conn.close()

# Função para configuaração de DNS
def dns_config(config_dict):
    
    # Aplica a configuração
    if config_dict["action"] == "apply":
        os.system("echo '#{}' >> /etc/resolv.conf".format(config_dict["rule_hash"]))
        os.system("echo 'nameserver {}' >> /etc/resolv.conf".format(config_dict["fields"]["address"]))

# Função de configuraç~ao de ipv4
def ipv4_config(config_dict):
    
    # Aplica a configuração
    if config_dict["action"] == "apply":
        os.system("uci set network.{}.ipaddr='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["address"]))
        os.system("uci set network.{}.netmask='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["netmask"]))
        os.system("uci set network.{}.gateway='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["gateway"]))
        os.system("uci set network.{}.dns='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["dns"]))
        
        os.system("uci commit network")
        os.system("/etc/init.d/network restart")
        

# Função de configuração de DHCP
def dhcp_config(config_dict):
    
    # Aplica a configuração
    if config_dict["action"] == "apply":
        os.system("uci set dhcp.{}.interface='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["interface"]))
        os.system("uci set dhcp.{}.start='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["start"]))
        os.system("uci set dhcp.{}.limit='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["limit_dhcp"]))
        os.system("uci set dhcp.{}.leasetime='{}'".format(config_dict["fields"]["interface"], config_dict["fields"]["leasetime"]))
        
        os.system("uci commit dhcp")
        os.system("/etc/init.d/odhcpd restart")

# Função para configuração de QoS
def qos_config(config_dict):
    
    # Dicionário com o texto associado a configuração de todos os parâmetros suportados
    qos_config = {"header":"config interface ",
                    "enabled":"\toption enabled\t",
                   "classgroup":"\toption classgroup\t",
                   "overhead":"\toption overhead\t",
                   "upload":"\toption upload\t",
                   "download":"\toption download\t"}
    
    # Coloca o identificados da configuração no arquivo
    os.system("echo '\n#{}' >> {}".format(config_dict["rule_hash"],"/etc/config/qos"))
    # Coloca o cabeçalho da regra
    os.system("echo '{}+{}' >> {}".format(qos_config["header"], config_dict["interface"], "/etc/config/qos"))
    
    configs = config_dict.keys()
    
    # Loop para inserção dos parâmetros da regras a partir do que foi enviado
    for config in configs:
        try:
            # Insere as configurações no arquivo do firewall
            os.system("echo '{}\t{}' >> {}".format(qos_config[config],config_dict[config],"/etc/config/qos"))

        except KeyError:
            pass
    
    # Reinicializa o serviço
    os.system("/etc/init.d/qos restart")
    
# Função para configuração de RIP
def RIP_config(config_dict):
    
    # Dicionário com o texto associado a configuração de todos os parâmetros suportados
    RIP_config = {"header":"config route ",
                    "interface":"\toption interface\t",
                   "target":"\toption target\t",
                   "netmask":"\toption netmask\t",
                   "gateway":"\toption gateway\t"}
    
    # Coloca o identificados da configuração no arquivo
    os.system("echo '\n#{}' >> {}".format(config_dict["rule_hash"],"/etc/config/network"))
    # Coloca o cabeçalho da regra
    os.system("echo '{}+{}' >> {}".format(RIP_config["header"], config_dict["route_id"], "/etc/config/network"))

    configs = config_dict.keys()
    
    # Loop para inserção dos parâmetros da regras a partir do que foi enviado
    for config in configs:
        try:
            # Insere as configurações no arquivo do firewall
            os.system("echo '{}\t{}' >> {}".format(RIP_config[config],config_dict[config],"/etc/config/network"))

        except KeyError:
            pass
    
    # Reinicializa o serviço
    os.system("/etc/init.d/network restart")
        
# Função para configuração de dhcp_relay
def dhcp_relay_config(config_dict):
    
    # Dicionário com o texto associado a configuração de todos os parâmetros suportados
    dhcp_relay_config = {"header":"config relay ",
                    "interface":"\toption interface\t",
                   "local_addr":"\toption local_addr\t",
                   "server_addr":"\toption server_addr\t"}
    
    # Coloca o identificados da configuração no arquivo
    os.system("echo '\n#{}' >> {}".format(config_dict["rule_hash"],"/etc/config/dhcp"))
    # Coloca o cabeçalho da regra
    os.system("echo '{}+{}' >> {}".format(dhcp_relay_config["header"], config_dict["id_relay"], "/etc/config/dhcp"))

    configs = config_dict.keys()
    
    # Loop para inserção dos parâmetros da regras a partir do que foi enviado
    for config in configs:
        try:
            # Insere as configurações no arquivo do firewall
            os.system("echo '{}\t{}' >> {}".format(dhcp_relay_config[config],config_dict[config],"/etc/config/dhcp"))

        except KeyError:
            pass
    
    # Reinicializa o serviço
    os.system("/etc/init.d/odhcpd restart")


# Função que cria o script a ser executado pela crontab  
def cron_create(rule):
    
    # Pega a assinatura da regra recebida
    rule_hash = rule["rule_hash"]
    # Pega o campo schedule da regra
    rule_schedule = rule["schedule"]
    # Cria dicionário com todos os campos necessários
    cron_dict = {"dayofweek":rule_schedule["dayofweek"],
                 "month":rule_schedule["month"],
                 "dayofmonth":rule_schedule["dayofmonth"],
                 "hour":rule_schedule["hour"],
                 "minute":rule_schedule["minute"]}
    
    
    # Pega o caminho do sistema de arquivos onde o script temporário será criado
    pwd_path = pathlib.Path.cwd()
    
    # Cria o corpo a ser executado para reenviar a requisição para /config, remover o registro do arquivo crontab e remover o script
    structure = """
    requested = requests.post("http://{}:{}/config".format(daemon_config["address"],daemon_config["port"]), json=rule)
    os.system("sed -e '/{}/,+1d' -i /etc/crontabs/root".format(rule["rule_hash"]))
    os.system("rm {}/{}.py".format(pwd_path,rule["rule_hash"]))
    """
    
    # Pega as informações necessárias para o script e transforma em JSON
    daemon_config = startup_process()
    config_json = json.dumps(daemon_config)
    
    # Adiciona o campo para identificar que está enviando pela cron
    rule["cron"] = "yes"
    
    rule_json = json.dumps(rule)
    
    # Cria o script a ser executado
    os.system("echo 'import os\nimport requests\nimport daemon_utils\n\n\nrule = {}\npwd_path = {}\ndaemon_config = {}\n\n\nif __name__ == \"{}\":\n' > ./{}.py".format(rule_json,str('"'+str(pwd_path)+'"'),config_json,str("__main__"),rule_hash))
    os.system("echo '{}' >> ./{}.py".format(structure, rule_hash))
    

    
    # Popula a crontab com o arquivo a ser executado
    os.system("echo '#{}' >> /etc/crontabs/root".format(rule_hash))
    os.system("echo '{} {} {} {} {} python3 {}/{}.py' >> /etc/crontabs/root".format(cron_dict["dayofweek"],
                                                                                   cron_dict["month"],
                                                                                   cron_dict["dayofmonth"],
                                                                                   cron_dict["hour"],
                                                                                   cron_dict["minute"],
                                                                                   pwd_path,
                                                                                   rule_hash))


    

if __name__ == "__main__":
    # payload = {
    #             "name":"Reject LAN to WAN for custom IP",
    #             "src":"lan",
    #             "dest":"wan",
    #             "proto":"icmp",
    #             "target":"REJECT"
    #         }
    
    # rule = {
    #     "action":"delete",
    #     "type":"fw",
    #     "fields":payload,
    #     "port":65004,
    #     "targets":"192.168.0.1",
    #     "schedule":{
    #         "minute":1,                 
    #         "enable": 1,
    #         "dayofmonth": 10,
    #         "month": 11,
    #         "dayofweek": 12,
    #         "hour":10
    #     },
    #     "rule_hash":"abcdfefgh12353"
    # }
    
    # if rule["action"] == "apply":
    #     # Cria query para inserçãõ no DB
    #     result = create_query_config(rule)
    #     if rule["type"] == "fw":
    #         apply_firewall_config(rule["fields"],rule["rule_hash"])
    #     apply(result)
    # elif rule["action"] == "delete":
    #     delete_config(rule["rule_hash"],rule["type"])
    
    rule = {'action': 'apply', 'type': 'fw', 'fields': {'name': 'Reject LAN to WAN for custom IP', 'src': 'lan', 'dest': 'wan', 'proto': 'icmp', 'target': 'REJECT', 'src_port': 5000, 'src_ip': '192.168.0.5'}, 'port': 50000, 'schedule': {'hour': 10, 'minute': 1, 'enable': 1, 'dayofmonth': 10, 'month': 11, 'dayofweek': 12}, 'targets': '127.0.0.1', 'rule_hash': '5bc154286a6275bb2c3562cb40714cd8', 'token': '97ea8fd3bf30f000a9faf79032d355f3'}
    cron_create(rule)
    