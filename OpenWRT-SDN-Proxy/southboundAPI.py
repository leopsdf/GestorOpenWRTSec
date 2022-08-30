import sys
#import pyof.openflow_utils as openflow
import socket
import requests
from flask import Flask, request, jsonify, redirect, url_for
import southutils
import json
import os
import northutils
import db_daemon


app = Flask(__name__)

# Função que realiza o processamento da configuração enviada para o OpenWRT gerenciado
def db_recv(socket_config):
    
    print(socket_config)
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Inicializando o socket
        s.bind((socket_config["address"], socket_config["port"]))
        s.listen()
        # Loop que aguarda conexões
        while True:
            conn,addr = s.accept()
            b = b''
            # Loop para recebimento de dados
            while True:
                data = conn.recv(32768)
                if not data:
                    print("INFO - Sem dados...")
                    break
                #conn.sendall(b"OK")
                
                # Concatenando os dados binários recebidos
                b += data
                
                # Convertendo em JSON
                try:
                    received_dict = json.loads(b.decode('utf-8'))
                    request = requests.post("http://"+received_dict["targets"]+":{}/config".format(received_dict["port"]), json=received_dict)
                    
                except json.decoder.JSONDecodeError as err:
                    pass
                except requests.HTTPError as err:
                    pass
                except requests.ConnectionError as err:
                    pass
                except requests.Timeout as err:
                    pass
                except requests.ConnectTimeout as err:
                    pass
                
                # # Realiza o processamento da configuraçaõ
                # process_recv_configs(received_dict)
                # break
            
                # Finalizando a conexão
            conn.close()

# Rota que remove todos os registros do dispositivo
@app.route("/deauth",methods=['POST'])
def southbound_deauth():
    
    # Pega o corpo do POST
    post_data = request.get_json(force=True)
    print(post_data)
    
    # Verifica os parâmetros
    check_result = southutils.check_deauth_params(post_data)
    if check_result[0]:
        
        known_tokens = southutils.get_known_tokens()
        # Verifica se o token está cadastrado
        if post_data["token"] in known_tokens:
            
            # Carrega a configuração do banco de dados
            db_config = db_daemon.startup_db()
        
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
                # Se conecta com o db_daemon
                s.connect((db_config["address"], db_config["port"]))
                
                # Insere a tag global para identicação no db_daemon
                post_data["global"] = "deauth"
                
                # Transforma o json a ser enviado em um tipo serializado para o socket
                send_data = json.dumps(post_data).encode('utf-8')
            
                # Manda o dicionário da query
                s.sendall(send_data)
                
            return jsonify({"STATUS":"SUCCESS"})
        
        else:
            
            return jsonify({"STATUS":"ERROR","INFO":"Token doesn't exists"})
            
        return check_result[1]
        
    else:
        return check_result[1]

# Rota para mudança de ip's nos dispostivos gerenciados
# recebe o novo IP e porta e identifica o host por alguma chave
@app.route("/switch",methods=['POST'])
def southbound_switch():
    # Pega o corpo do POST
    post_data = request.get_json(force=True)
    
    # Verifica os parâmetros
    check_result = southutils.check_switch_params(post_data)
    if check_result[0]:
        
        known_tokens = southutils.get_known_tokens()
        # Verifica se o token está cadastrado
        if post_data["token"] in known_tokens:
            
            # Verifica se o novo token não existe
            if post_data["new_token"] not in known_tokens:
        
                # Carrega a configuração do banco de dados
                db_config = db_daemon.startup_db()
        
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
                    # Se conecta com o db_daemon
                    s.connect((db_config["address"], db_config["port"]))
                    
                    # Insere a tag global para identicação no db_daemon
                    post_data["global"] = "switch"
                    
                    # Transforma o json a ser enviado em um tipo serializado para o socket
                    send_data = json.dumps(post_data).encode('utf-8')
                
                    # Manda o dicionário da query
                    s.sendall(send_data)
            
                return jsonify({"STATUS":"SUCCESS"})
            else:
                
                return jsonify({"STATUS":"ERROR","INFO":"new_token already exists"})
        else:
            
            return jsonify({"STATUS":"ERROR","INFO":"Token doesn't exists"})
            
        return check_result[1]
        
    else:
        return check_result[1]

# TODO colococar o token criado junto com o auth
# Rota para autenticação de dispositivos gerenciados
@app.route("/auth", methods=['POST'])
def southbound_auth():
    # Coloca em formato de dicionário
    post_data = request.get_json(force=True)
    
    print(post_data)
    
    # Verifica os parâmetros recebidos
    check_result = southutils.check_auth_params(post_data)
    if check_result[0]:
        
        known_tokens = southutils.get_known_tokens()
        # Verifica se o token já foi cadastrado
        if post_data["token"] not in known_tokens:
        
            # Carrega a configuração do banco de dados
            db_config = db_daemon.startup_db()
        
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
                # Se conecta com o db_daemon
                s.connect((db_config["address"], db_config["port"]))
                
                # Insere a tag global para identicação no db_daemon
                post_data["global"] = "auth"
                
                # Transforma o json a ser enviado em um tipo serializado para o socket
                send_data = json.dumps(post_data).encode('utf-8')
            
                # Manda o dicionário da query
                s.sendall(send_data)
                
            return jsonify({"STATUS":"SUCCESS"})
        
        else:
            
            return jsonify({"STATUS":"ERROR","INFO":"Token already exists"})
            
        return check_result[1]
        
    else:
        return check_result[1]
    
def get_db_config():
    
    # Pega os parâmetros de inicialização do db_daemon
    config_db = configparser.ConfigParser()
    config_db.read("configs/db_daemon.ini")
    
    host = config_db["CONFIG"]["HOST"]
    port = config_db["CONFIG"]["PORT"]
    
    return [host,port]

# Função para inciar a southbound interface
def southbound_main(south_config):
    
    pid = os.fork()
    if pid > 0:
        print(south_config)
        app.run(debug=True, host=south_config[0]["address"], port=south_config[0]["port"])
        
    else:
        db_recv(south_config[1])

if __name__ == "__main__":
    
    # Carrega as configurações da interface southbound
    south_config = southutils.startup_south()
    
    # Incializa a interface sul
    southbound_main(south_config)