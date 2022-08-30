from flask import Flask, request, jsonify, redirect, url_for
import requests
import json
import daemon_utils
import sqlite3
import create_token

app = Flask(__name__)

@app.route("/config",methods=["POST"])
def openwrt_recv_config():
    # Coloca em formato de dicionário
    post_data = request.get_json(force=True)
    rule = dict(post_data)
    
    print(rule)
    
    startup_config = daemon_utils.startup_process()
    
    # Verifica se o token de autenticação é válido
    if rule["token"] == startup_config["token"]:
    
        # Aplica a configuração recebida
        if rule["action"] == "apply":
            
            # Cria query para inserçãõ no DB
            query = daemon_utils.create_query_config(rule)
            
            if rule["type"] == "fw":
                # Aplica configa para firewall
                daemon_utils.apply_firewall_config(rule["fields"],rule["rule_hash"])
                
            elif rule["type"] == "dhcp":
                # Aplica a configuração para DHCP
                daemon_utils.dhcp_config(rule)
            
            elif rule["type"] == "dhcp_static":
                pass
            
            elif rule["type"] == "dhcp_relay":
                # Aplica a configuração de dhcp_relay
                daemon_utils.dhcp_relay_config(rule)
            
            elif rule["type"] == "ipv4":
                # Aplica configuração de ipv4
                daemon_utils.ipv4_config(rule)
            
            elif rule["type"] == "RIP":
                # Aplica a configuração de RIP
                daemon_utils.RIP_config(rule)
            
            elif rule["type"] == "QoS":
                # Aplica configurações de QoS
                daemon_utils.qos_config(rule)
            
            elif rule["type"] == "DNS":
                # Aplica a configuração do DNS
                daemon_utils.dns_config(rule)
                
            # Aplica a query de inserção no banco de dados
            daemon_utils.apply(query)
        
        # Remove a configuração recebida
        elif rule["action"] == "delete":
            daemon_utils.delete_config(rule["rule_hash"],rule["type"],rule)
                
            
    else:
        return "False"
    
    
    return "Success"

# Veririca se o usuário já está autenticado
def try_auth(config_dict):
    
    controller_config = daemon_utils.controller_config()
    print("INFO - Trying to authenticate to: {}:{}\n".format(controller_config["address"],
                                                           controller_config["port"]))
    
    auth_payload = {"address":config_dict["address"],
                    "port":config_dict["port"],
                    "netmask":config_dict["netmask"],
                    "token":config_dict["token"]}
    
    
    try:
        requested = requests.post("http://{}:{}/auth".format(controller_config["address"],controller_config["port"]), json=auth_payload)
        
        response = json.loads(requested.text)
        print(response)
        
        if response["STATUS"] == "ERROR":
            print("ERROR - Couldnt authenticate to the controller.")
        
        else:
            print("INFO - Auth Success")
            
            # Se conecta ao banco de dados
            conn = sqlite3.connect("database/host_config.db")
            cursor = conn.cursor()
            # Atualiza o status de autenticação
            cursor.execute("update host set auth = \"{}\" where id = 1;".format(1))
            
            conn.commit()
            conn.close()
    
    except requests.HTTPError as err:
        print(err)
    except requests.ConnectionError as err:
        print(err)
    except requests.Timeout as err:
        print(err)
    except requests.ConnectTimeout as err:
        print(err)


if __name__ == "__main__":
    
    # TODO fazer a CLI para config
    
    startup_config = daemon_utils.startup_process()
    print("INFO - Startup config: {}".format(startup_config))
    
    # # Pega as informações do arquivo de configuração    
    # start_info = startup_process()
    # print(start_info)
    
    # # FAZER PROCESSAMENTO DA CRONTAB
    
    # Verifica se já existe um token
    if startup_config["token_status"] == 0:
        token = create_token.create()
        # Coloca o token na base de dados
        create_token.update_token(token)
    
    new_startup_config = daemon_utils.startup_process()
    # Verifica se já está autenticado
    if startup_config["auth"] == 0:
        try_auth(new_startup_config)
    
    # # Inicializa a API do daemon
    app.run(debug=True, host=startup_config["address"], port=new_startup_config["port"])    
