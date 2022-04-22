import jwt
import sqlite3
from collections import OrderedDict
import hashlib
import json
import ipaddress
import socket
import pickle
import time

########################### Utility functions used on the API paths ##############################

possible_configs = ["ipv4","dhcp","dhcp_static","dhcp_relay","RIP","QoS","DNS","fw"]

# INFO do socket db_daemon (recebimento de configs)
HOST = "127.0.0.1"
PORT = 65001

# Reads the key file and returns it's contents in byte format, ready to be used for SSL or JWT token encoding
def get_key(file_name):
    key =""
    with open(str(file_name), 'rb') as file:
        key = file.read()
        file.close()
        
    return key


# Return array - [0] true if decoded successfully or false if error, [1] decoded jwt if true or error message if false
def attempt_jwt_decode(jwt_token, pub_key):
    try:
        decoded_jwt_token = jwt.decode(jwt_token, pub_key, algorithms="RS256")
        return [True, decoded_jwt_token]
    except jwt.exceptions.InvalidTokenError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    except jwt.exceptions.DecodeError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    except jwt.exceptions.InvalidSignatureError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    except jwt.exceptions.ExpiredSignatureError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    
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
        field_string += field+ordered_fields[field]
    
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
        target_string += target + rule_dict["targets"][target][0]
    
    # Ordena as chaves do campo schedule em ordem alfabética, para que assim
    # caso sejam enviadas em ordem diferente não haja mudança no hash da regra
    ordered_schedules = OrderedDict(sorted(rule_dict["schedule"].items()))
    
    # Loop de criação da string associada ao campo schedule
    schedule_string = ""
    for schedule in ordered_schedules.keys():
        schedule_string += schedule+str(ordered_schedules[schedule])
        
    # Criação da string final associada a regra        
    final_string = action_string+type_string+field_string+target_string+schedule_string
    
    # Hash md5 da string final
    md5_hash = hashlib.md5(final_string.encode('utf-8')).hexdigest()
    
    # Insere a chave rule_hash com o hash criado
    rule_dict["rule_hash"] = md5_hash
    
    return rule_dict
    
    
# Classes responsável pelo processamento das conigurações recebidas.
# Checagem de parâmetros, aplicação e deleção de regras
class Config():
    
    def __init__(self, config_json):
           self.config_body = config_json
    
    # Função feita para checar se os parâmetros enviados são válidos
    def check_parameters_rule(self, known_parameters):
        # Lista com todos os parâmetros para qualquer tipo de regra
        rule_parameters = ["action","JWT","who","timestamp","type","fields","targets","schedule"]
        # Inicializa o contador de parâmetros
        parameter_counter = 0
        # Loop que verifica se os campos enviados são estão dentro dos válidos
        for rule_param in self.config_body.keys():
            if rule_param not in rule_parameters:
                return False
            parameter_counter += 1
        
        # Se a quantidade de parâmetros enviados diferente da quantidade obrigatória
        if parameter_counter != len(rule_parameters):
            return False
        
        # Pega um array com o nome de todas as configurações
        known_configs_keys = known_parameters.keys()
        
        # Se o tipo de configuração recebido não estiver entre
        # as válidas retorne False
        if self.config_body["type"] not in known_configs_keys:
            return False
        
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
                return False
            

        # Loop de verificação das configurações de agendamento
        schedule_keys = ["enable","minute","month","dayofweek","hour","dayofmonth"]
        schedule_recv_keys = self.config_body["schedule"].keys()
        for schedule in schedule_recv_keys:
            if schedule not in schedule_keys:
                return False
        
        # Se estiverem faltando campos retorne Falso
        if len(schedule_recv_keys) != len(schedule_keys):
            return False    
        
        # Se chegar até aqui a configuração é válida
        return True
    
    # Método utilizado para checar a validez de uma criação de grupo lógico
    def check_target(self):
        print("placeholder") 
    
    # Método utilizado para enviar a configuração recebida para o db_daemon   
    def send(self,config_array):
        
        # Loop para envio individual de cada uma das regras
        for config in config_array:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT)) # conecta ao servidor
            send_data = json.dumps(config).encode('utf-8')
            s.sendall(send_data) # manda a mensagem
            time.sleep(0.01)
            s.close()           
            
            # #print("Enviar regra para o socket do serviço de inserção no banco") # Será que vai demorar muito com muitas regras? Buscar no banco não seria melhor?
                # with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
                #     s.connect((HOST, PORT)) # conecta ao servidor
                #     send_data = json.dumps(post_data).encode('utf-8')
                #     s.sendall(send_data) # manda a mensagem
        