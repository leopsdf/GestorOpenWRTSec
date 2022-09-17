import jwt
import sqlite3
from collections import OrderedDict
import hashlib
import json
import ipaddress
import socket
import pickle
import time
from flask import jsonify
import db_daemon
import random
import string

########################### Utility functions used on the API paths ##############################

possible_configs = ["ipv4","dhcp","dhcp_static","dhcp_relay","RIP","QoS","DNS","fw"]

# Reads the key file and returns it's contents in byte format, ready to be used for SSL or JWT token encoding
def get_key(file_name):
    key =""
    with open(str(file_name), 'rb') as file:
        key = file.read()
        file.close()
        
    return key

# Cria o token utilizado na autenticação
def create():
    # Cria um array de letras pseudo-aleatórias
    random_letters = random.choices(string.ascii_lowercase, k=150)
    
    token_string = ""
    # Constroi a string random com os caracteres gerados
    for letter in random_letters:
        token_string += letter
    
    # token final em formato md5
    token = hashlib.md5(token_string.encode('utf-8')).hexdigest()
    
    return token

def update_token(token):
    
    # Pega a porta do dispositivo gerenciado
    conn = sqlite3.connect("database/controller.db")
    cursor = conn.cursor()
    # Atualiza o registro do host
    cursor.execute("update northboundAPI set token = \"{}\" where id = 1;".format(token))
    
    conn.commit()
    conn.close()

# Coleta as informações de inicialização da northboundAPI
def startup_north():
    
    # Se conecta ao banco de dados do controller
    conn = sqlite3.connect("database/controller.db")
    cursor = conn.cursor()
    # Pega as configurações da northboundAPI
    cursor.execute("select * from northboundAPI where id = 1;")
    result = cursor.fetchall()
    
    # Dicionários das configs
    startup_config = {"port":int(result[0][1]),
                      "address":result[0][2],
                      "token":result[0][3]}
    
    conn.close()
    
    return startup_config


# Return array - [0] true if decoded successfully or false if error, [1] decoded jwt if true or error message if false
def attempt_jwt_decode(jwt_token, pub_key):
    try:
        decoded_jwt_token = jwt.decode(jwt_token, pub_key, algorithms="RS256")
        return [True, decoded_jwt_token]
    except jwt.exceptions.InvalidTokenError as err:
        #err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, str(err)]
    except jwt.exceptions.DecodeError as err:
        #err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, str(err)]
    except jwt.exceptions.InvalidSignatureError as err:
        #err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, str(err)]
    except jwt.exceptions.ExpiredSignatureError as err:
        #err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, str(err)]
    
# Função que carrega na memória todos os parâmetros aceitados
# para cada configuração possível.
def load_all_possible_parameters():
    # json com as configurações possíveis
    parameters_json = {}
        
    # conexão no banco de dados das informações de configurações
    conn = sqlite3.connect("database/configs_parameters.db")
    cursor = conn.cursor()
    
    # loop para pegar os parâmetros de cada tipo de configuração
    for config_name in possible_configs:
        cursor.execute("select config_name from {};".format(config_name))
        result = cursor.fetchall()
        parameters_json[config_name] = result
            
    return parameters_json  

# Função que pega os hashes de todas as configurações
# cadastradas no banco de dados e retorna em uma array
def load_all_applied_configs():
    # array com todos os hashes cadastrados
    configs = []
    
    # conexão com o banco de dados de configurações
    conn = sqlite3.connect("database/configs.db")
    cursor = conn.cursor()
    
    # loop para pegar o hash das configurações de cada tipo e os colocar em um array
    for config_name in possible_configs:
        cursor.execute("select rule_hash from {};".format(config_name))
        results = cursor.fetchall()
        for result in results:
            configs.append(result)
            
    return configs

# Função que carrega em memória todos os grupos criados
def load_all_groups():
    groups = []
    
    # conexão com o banco de dados de configurações
    conn = sqlite3.connect("database/hosts_groups.db")
    cursor = conn.cursor()
    
    # Pega os nomes dos grupos criados do banco de dados da tabela groups
    cursor.execute("select group_name from groups;")
    groups_prior = cursor.fetchall()
    
    for group in groups_prior:
        groups.append(group[0])
    conn.close()
    
    return groups

# Função que pega no banco de dados os hosts cadastrados.
# Não coloca em memória pois podem ter inserções enquanto
# a API está em execução
def load_all_hosts():
    hosts = []
    
    conn = sqlite3.connect("database/hosts_groups.db")
    cursor = conn.cursor()
    
    # Pega os endereços de todos os hosts cadastrados na ferramenta    
    cursor.execute("select address from openwrt;")
    hosts_prior = cursor.fetchall()
    
    for host in hosts_prior:
        hosts.append(host[0])
    
    conn.close()
    
    return hosts

# Função que carrega em memória todas relações grupos
# hosts existentes
def load_host_group_relation(known_groups):
    host_group_relation = {}
    
    conn = sqlite3.connect("database/hosts_groups.db")
    cursor = conn.cursor()
    
    # Pega os endereços de todos os hosts pertencentes a todos os grupos existentes 
    for group in known_groups:
        cursor.execute("select address from openwrt where group_name = \"{}\";".format(str(group)))
        hosts_prior = cursor.fetchall()
        hosts = []
        for host in hosts_prior:
            hosts.append(host[0])
            
        host_group_relation[group] = hosts
        
    return host_group_relation

# Função que recebe o dicionário da regra a ser cadastrada e utiliza campos relevantes
# para criar um hash, servindo como identificador único daquela regra. Utilizada para
# verificar a existência de uma regra sem consulta ao banco. 
#
# Retorna o dicionário decebido com um novo campo "rule_hash"
def hash_rule(rule_dict):
    # Cria a string associada ao campo action
    action_string = "action"+rule_dict["action"]
    
    # Cria a string associada ao campo type
    type_string = "type"+rule_dict["type"]
    
    # Ordena as chaves do campo fields em ordem alfabética, para que assim
    # caso sejam enviadas em ordem diferente não haja mudança no hash da regra
    ordered_fields = OrderedDict(sorted(rule_dict["fields"].items()))
    
    # Loop de criação da string associada ao campo fields
    field_string = ""
    for field in ordered_fields.keys():
        field_string += field+str(ordered_fields[field])
    
    # Ordena as chaves do campo targets em ordem alfabética, para que assim
    # caso sejam enviadas em ordem diferente não haja mudança no hash da regra
    ordered_targets = OrderedDict(sorted(rule_dict["targets"].items()))

    # Loop de criação da string associada ao campo targets
    target_string = ""
    # for target in ordered_targets.keys():
    #     target_string += target
    #     # Realiza a ordenação de ip's dentro da lista associada a uma entidade lógica, 
    #     # isso é feito para que não haja mudança no hash caso a ordem seja modificada
    #     ordered_targets[target] = sorted(ordered_targets[target], key=ipaddress.IPv4Address)
    #     for entity in ordered_targets[target]:
    #         target_string += entity
    target_keys = rule_dict["targets"].keys()
    for target in target_keys:
        #target_string += target + rule_dict["targets"][target][0]
        target_string += rule_dict["targets"][target][0]
    
    # Ordena as chaves do campo schedule em ordem alfabética, para que assim
    # caso sejam enviadas em ordem diferente não haja mudança no hash da regra
    ordered_schedules = OrderedDict(sorted(rule_dict["schedule"].items()))
    
    # Loop de criação da string associada ao campo schedule
    schedule_string = ""
    for schedule in ordered_schedules.keys():
        if schedule != "hour":
            schedule_string += schedule+str(ordered_schedules[schedule])
        
    # Criação da string final associada a regra        
    final_string = action_string+type_string+field_string+target_string+schedule_string
    #final_string = type_string+field_string+target_string+schedule_string
    
    # Hash md5 da string final
    md5_hash = hashlib.md5(final_string.encode('utf-8')).hexdigest()
    
    # Insere a chave rule_hash com o hash criado
    rule_dict["rule_hash"] = md5_hash
    
    return rule_dict

# Função que envia via socket as queries de listagem pro banco de dados processar.
# Recebe de volta um dicionário com todos os resultados presentes no banco baseado no filtro.
# query_type = host_list e config_list
# params = dicionário com todos os filtros a serem utilizados (ver em cada rota de listagem da API o padrão para os tipos de query)
# sub_cofig = tipo da configuração (dhcp,dhcp_relay,dhcp_static,ipv4,dnv,rip,qos,iptables)
def send_list_query_to_db(query_type,params,sub_config):
    
    # verifica se o tipo da listagem é para um configuração, que teria um sub_config diferente de none
    if sub_config == None:
        config = {'global':query_type,'params':params}
    else:
        config = {'global':query_type,'params':params,'sub_config':sub_config}
        
    # Carrega as configurações do db_daemon
    db_config = db_daemon.startup_db()
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
        # Se conecta com o db_daemon
        s.connect((db_config["address"], db_config["port"]))
        
        # Transforma o json a ser enviado em um tipo serializado para o socket
        send_data = json.dumps(config).encode('utf-8')
        
        # Manda o dicionário da query
        s.sendall(send_data)
        
        result_array = []
        while True:
            
            # Cria o tipo byte que vai receber a resposta
            b = b''
            # Lê a resposta do servidor
            data = s.recv(32768)
        
            # Concatena com o formato de bytes
            b += data
            try:
                # Transforma os bytes recebidos no formato json para ser retornado como dicionário
                received_dict = json.loads(b.decode('utf-8'))
            except json.decoder.JSONDecodeError as err:
                    pass
            
            
            try:
                # Verifica se o último resultado da busca já foi enviado
                if received_dict["Status"] == "End":
                    break
            except KeyError as err:
                pass
            
            # Coloca os resultados dentro de um array
            result_array.append(received_dict)
            
        # Retorna o array de resultados para a API
        return result_array
        
    
# Classes responsável pelo processamento das conigurações recebidas.
# Checagem de parâmetros, aplicação e deleção de regras
class Config():
    
    def __init__(self, config_json):
           self.config_body = config_json
    
    # Função feita para checar se os parâmetros enviados são válidos
    def check_parameters_rule(self, known_parameters):
        # Lista com todos os parâmetros para qualquer tipo de regra
        rule_parameters = ["action","token","who","timestamp","type","fields","targets","schedule"]
        # Inicializa o contador de parâmetros
        parameter_counter = 0
        # Loop que verifica se os campos enviados são estão dentro dos válidos
        for rule_param in self.config_body.keys():
            if rule_param not in rule_parameters:
                return [False,"Not all rule parameters were sent"]
            parameter_counter += 1
        
        # Pega um array com o nome de todas as configurações
        known_configs_keys = known_parameters.keys()
        
        # Se o tipo de configuração recebido não estiver entre
        # as válidas retorne False
        if self.config_body["type"] not in known_configs_keys:
            return [False,"Unkown config type"]
        
         # Se a quantidade de parâmetros enviados diferente da quantidade obrigatória
        if self.config_body["type"] == "fw":
            if "name" not in self.config_body["fields"].keys():
                return [False,"'name' parameter is necessary for firewall configuration"]
            
            # Verifica se o src e dest são wan ou lan
            if "src" in self.config_body["fields"].keys():
                if self.config_body["fields"]["src"] != "lan" and self.config_body["fields"]["src"] != "wan":
                    return [False,"'src' must be either wan or lan"]

            if "dest" in self.config_body["fields"].keys():
                if self.config_body["fields"]["dest"] != "lan" and self.config_body["fields"]["dest"] != "wan":
                    return [False,"'dest' must be either wan or lan"]
            
            pass
        elif parameter_counter != len(rule_parameters):
            return [False,"Not all required rule fields were sent"]
        
        # Pega os parâmetros possíveis dessa configuração
        known_config = known_parameters[self.config_body["type"]]
        
        known_configs = []
        for config in known_config:
            config_name = config[0]
            known_configs.append(config_name)
        
        # Pega os parâmetros enviados pelo administrador
        sent_parameters = self.config_body["fields"].keys()
        
        # Neste loop é verificada a existência de cada parâmetro
        # enviado dentre o conjunto de possíveis
        for parameter in sent_parameters:
            if parameter not in known_configs:
                return [False,"Parametes {} is not valid for this config type".format(parameter)]
            

        # Loop de verificação das configurações de agendamento
        schedule_keys = ["enable","minute","month","dayofweek","hour","dayofmonth"]
        schedule_recv_keys = self.config_body["schedule"].keys()
        for schedule in schedule_recv_keys:
            if schedule not in schedule_keys:
                return [False,"Schedule parameter {} not supported".format(schedule)]
        
        # Se estiverem faltando campos retorne Falso
        if len(schedule_recv_keys) != len(schedule_keys):
            return [False,"Not all schedule keys were sent"]    
        
        # Se chegar até aqui a configuração é válida
        return [True,"Success"]
    
    # Método utilizado para checar a validez de uma criação de grupo lógico
    def check_group(self, known_groups):
        group_parameters = ["action","token","who","timestamp","group_name"]
        
        # Inicializa o contador de parâmetros
        parameter_counter = 0
        # Loop que verifica se os campos enviados são estão dentro dos válidos
        for group_param in self.config_body.keys():
            if group_param not in group_parameters:
                return False
            parameter_counter += 1
        
        # Se a quantidade de parâmetros enviados diferente da quantidade obrigatória
        if parameter_counter != len(group_parameters):
            return False
        
        # Fazer a verificação da existência do grupo (delete) ou duplicata (create)
        if self.config_body["action"] == "create":
            if self.config_body["group_name"] in known_groups:
                return False
        elif self.config_body["action"] == "delete":
            if self.config_body["group_name"] not in known_groups:
                return False
        else:
            return False
            
        return True
        
    # Método utilizado para checar a existência de um host e do grupo lógico
    def check_host(self, known_hosts, known_groups, known_host_group_relation):
        host_parameters = ["action","token","who","timestamp","group_name","targets"]
        
        # Inicializa o contador de parâmetros
        parameter_counter = 0
        # Loop que verifica se os campos enviados são estão dentro dos válidos
        for host_param in self.config_body.keys():
            if host_param not in host_parameters:
                print("1")
                return False
            parameter_counter += 1
        
        # Se a quantidade de parâmetros enviados diferente da quantidade obrigatória
        if parameter_counter != len(host_parameters):
            print("2")
            return False
        
        # Fazer a verificação da existência do grupo e do host (insert), se o host e grupo existem (update)
        # e se o host faz parte do grupo (delete)
        if self.config_body["action"] == "insert":
            if self.config_body["group_name"] not in known_groups:
                print("3")
                return False
            for target in self.config_body["targets"]:
                if target not in known_hosts:
                    print("4")
                    return False
            
        elif self.config_body["action"] == "delete":
            for target in self.config_body["targets"]:
                if target not in known_host_group_relation[self.config_body["group_name"]]:
                    print("5")
                    return False
                
        elif self.config_body["action"] == "update":
            if self.config_body["group_name"] not in known_groups:
                print("6")
                return False
            for target in self.config_body["targets"]:
                if target not in known_hosts:
                    print("7")
                    return False
        else:
            # Ação não suportada
            print("8")
            return False
            
        return True
    
    # Método utilizado para enviar a configuração recebida para o db_daemon   
    def send(self,config_array):
        
        # Carrega as configurações do db_daemon
        db_config = db_daemon.startup_db()
        
        # Loop para envio individual de cada uma das regras
        for config in config_array:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((db_config["address"], db_config["port"])) # conecta ao servidor
            send_data = json.dumps(config).encode('utf-8')
            s.sendall(send_data) # manda a mensagem
            time.sleep(0.01)
            s.close()           