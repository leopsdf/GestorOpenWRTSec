import socket
from flask import jsonify
import northutils
import sqlite3

# Coleta as informações de inicialização da interface south
def startup_south():
    
    # Pega a porta do dispositivo gerenciado
    conn = sqlite3.connect("database/controller.db")
    cursor = conn.cursor()
    # Coleta configurações do southboundAPI
    cursor.execute("select * from southboundAPI where id = 1;")
    result_API = cursor.fetchall()
    
    # Coleta configurações do southbound_socket
    cursor.execute("select * from southbound_socket where id = 1;")
    result_socket = cursor.fetchall()
    
    # Dicionários das configs
    startup_config = [{"port":int(result_API[0][1]),
                      "address":result_API[0][2]},
                      {"port":int(result_socket[0][1]),
                       "address":result_socket[0][2]}]
    
    conn.close()
    
    return startup_config

# Pega do banco de dados todas os tokens de hosts cadastrados
def get_known_tokens():
    
    # Se conecta ao banco de dados
    conn = sqlite3.connect("database/hosts_groups.db")
    cursor = conn.cursor()
    # Pega todos os tokens cadastrados
    cursor.execute("select token from openwrt;")
    result = cursor.fetchall()

    if len(result) == 0:
        result.append(" ")
        tokens = result
    else:
        # Lista com todos os token existentes 
        tokens = result[0]

    conn.close()
    
    return tokens

# Verifica os parâmetros de switch
def check_switch_params(payload):
    
    if not "token" in payload.keys():
        return [False,jsonify({"STATUS":"ERROR","INFO":"No token received."})]       
    
    if not "new_token" in payload.keys():
        return [False,jsonify({"STATUS":"ERROR","INFO":"No new_token received."})]  

    if len(payload.keys()) > 2:
        return [False,jsonify({"STATUS":"ERROR","INFO":"Aditional parameters besides token and new_token were sent."})] 
    
    return[True,jsonify({"STATUS":"SUCCESS","INFO":"Switch request received."})]

# Verifica os parâmetros do recebidos para deauth
def check_deauth_params(payload):
    
    if not "token" in payload.keys():
        return [False,jsonify({"STATUS":"ERROR","INFO":"No token received."})]
    
    if len(payload.keys()) > 2:
        return [False,jsonify({"STATUS":"ERROR","INFO":"Aditional parameters besides token were sent."})]
    
    # Verifica se o endereço IP é válido
    try:
        socket.inet_aton(payload["address"])
    except socket.error:
        return [False,jsonify({"STATUS":"ERROR","INFO":"address '{}' is not a valid IP.".format(payload["address"])})]
    
    return[True,jsonify({"STATUS":"SUCCESS","INFO":"Deauth request received."})]

# Verifica os parâmetros recebidos para auth
def check_auth_params(payload):
    # Verifica se o endereço IP é válido
    try:
        socket.inet_aton(payload["address"])
    except socket.error:
        return [False,jsonify({"STATUS":"ERROR","INFO":"address '{}' is not a valid IP.".format(payload["address"])})]
    
    # Verifica se o host já existe
    hosts = northutils.load_all_hosts()
    if payload["address"] in hosts:
        return [False,jsonify({"STATUS":"ERROR","INFO":"Host already registered"})]
    
    # Verifica se a porta é um inteiro
    try:
        port = int(payload["port"])
    except ValueError as err:
        return [False,jsonify({"STATUS":"ERROR","INFO":"port '{}' is not a number.".format(string(payload["port"]))})]
    
    # Verifica se o endereço IP é válido
    try:
        socket.inet_aton(payload["netmask"])
    except socket.error:
        return [False,jsonify({"STATUS":"ERROR","INFO":"netmask '{}' is not a valid IP.".format(payload["netmask"])})]
    
    return [True,jsonify({"STATUS":"SUCCESS","INFO":"Auth request received."})]