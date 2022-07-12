# Esse programa é responsável por subir uma porta tcp para 
# receber da interface northbound as configurações, sejam elas
# de regras ou de unidades lógicas de hosts (first_floor, guests, etc).
#
# Após o recebimento dessas regras as mesmas são inseridas no banco de dados
# e enviadas via TCP para a southbound API, para que possam ser traduzidas em openflow e 
# enviadas para os respectivos hosts, caso a ação determine isso.

import socket
import sqlite3
import json
import time

# INFO do socket db_daemon (recebimento de configs)
HOST = "127.0.0.1"
PORT = 65001

# INFO envio de configs para southbound
HOST_SOUTH = "127.0.0.1"
PORT_SOUTH = 65002

# INFO do socket de envio e recebimento de listagens da northboundAPI
HOST_LIST = "127.0.0.1"
PORT_LIST = 65003

# Classe principal do db_daemon, comprime todas as funções necessárias para o funcionamento da entidade
class DB_daemon():
    
    def __init__(self, config_db_file,rule):
        self.file = config_db_file
        self.rule = rule
           
    # Método utilizado para a criação das queries utilizadas para salvar a regra no banco para cada entidade (cada IP)    
    # Retorna um array com queries a serem aplicadas
    def create_query_config(self):
        
        # Nome da tabela definida pelo tipo da configuração
        table_name = self.rule["type"]
        # Define a primeira e segunda parte da query com os campos que não variam
        fist_part_query = "insert into {} (who,enable,minute,hour,dayofmonth,month,dayofweek,rule_hash".format(table_name)
        second_part_query = " values (\"{}\",{},{},{},{},{},{},\"{}\"".format(self.rule["who"],
                                                                              self.rule["schedule"]["enable"],
                                                                              self.rule["schedule"]["minute"],
                                                                              self.rule["schedule"]["hour"],
                                                                              self.rule["schedule"]["dayofmonth"],
                                                                              self.rule["schedule"]["month"],
                                                                              self.rule["schedule"]["dayofweek"],
                                                                              self.rule["rule_hash"])
        # Loop para inserção dos fields e seus valores na query da regra
        for field_name in self.rule["fields"].keys():
            fist_part_query += ",{}".format(field_name)
            second_part_query += ",\"{}\"".format(str(self.rule["fields"][field_name]))
            
        # Array que armazenará as queries criadas para cada entidade (regras separadas por ip's específicos)
        queries_array = []
        # Pega os nome dos grupos lógicos abordados na regra
        targets_logical_name = self.rule["targets"].keys()
        for logical_target in targets_logical_name:
            # Para cada endereço abordado dentro do grupo lógico criar uma regra a ser inserida
            for ip in self.rule["targets"][logical_target]:
                loop_first_part = fist_part_query
                loop_second_part = second_part_query
                # Adiciona os campos relativos ao grupo lógico e o endereço da entidade na query
                loop_first_part += ",logical_group,openwrt_ipv4"
                loop_second_part += ",\"{}\",\"{}\"".format(logical_target,str(ip))
                
                # Finaliza a query no formato esperado
                loop_first_part += ")"
                loop_second_part += ");"
                
                # Concatena as strings
                final_query = loop_first_part+loop_second_part
                
                # Coloca no array resultado
                queries_array.append(final_query)
                
        return queries_array
        
    # Cria query para criação de novos grupos lógicos
    def create_query_group(self):
        print("placeholder")
        
    # Cria query para cadastro de novas entidades    
    def create_query_openwrt(self):
        print("placeholder")
    
    # Função que executa queries recebidas (SOMENTE INSERT)
    def apply(self, queries_array):
        
        conn = sqlite3.connect(self.file)
        cursor = conn.cursor()
        
        # Executa todas as queries recebidas
        for query in queries_array:
            print(query)
            cursor.execute(query)

        # Salva as mudanças feitas
        conn.commit()
        conn.close()
    
    # Função que seleciona os hosts baseados no filro recebido e os formata em dicionário
    def apply_select_host(self,query):
        
        conn = sqlite3.connect(self.file)
        cursor = conn.cursor()
        
        # Executa a query
        cursor.execute(query)
        # Pega os resultados da query
        results = cursor.fetchall()
        
        # Se não houver resultados para o filtro aplicado retorne a mensagem abaixo
        if len(results) == 0:
            return [{"Response":"No hosts found"}]
        
        send_result = []
        # Loop de confecção de dicionários para resposta da requisição bem estruturada
        for result in results:
            dict_result = {"Address":result[1],"Port":result[2],"Netmask":result[3],"Group":result[4]}
            send_result.append(dict_result)
        
        return send_result
        

    # Função que executa queries recebidas (SOMENTE DELETE)
    def delete(self):
        conn = sqlite3.connect(self.file)
        cursor = conn.cursor()
        
        # Deleta a configuração utilizando como chave o hash gerado para a regra
        cursor.execute("delete from \"{}\" where rule_hash = \"{}\";".format(self.rule["type"],self.rule["rule_hash"]))
        
        conn.commit()
        conn.close()

# Função que pega a configuração recebida via socket e processa no DB
def process_recv_configs(received_dict):
    
    db = DB_daemon("database/configs.db", received_dict)
    if received_dict["action"] == "apply":
        # Criação de queries para inserção do db
        queries = db.create_query_config()
        # Execução dessas queries
        #print(queries)
        db.apply(queries)
        print("INFO - config aplicada")
    elif received_dict["action"] == "delete":
        # Remoção das configurações pelo hash identificador
        #print("delete")
        db.delete()

# Função que pega a configuração de grupo recebida via socket e processa no DB
def process_recv_groups(received_dict):

    db  = DB_daemon("database/hosts_groups.db", received_dict)
    if received_dict["action"] == "create":
        # Criação de query
        query = "insert into groups (group_name) values (\"{}\");".format(received_dict["group_name"])
        queries = [query]
        
    elif received_dict["action"] == "delete":
        # criação de query para deletar o grupo
        query_delete = "delete from groups where group_name = \"{}\";".format(received_dict["group_name"])
        # Colocar no grupo Default os hosts que estavam no grupo deletado
        query_update_hosts = "update openwrt set group_name = \"{}\" where group_name = \"{}\";".format("Default",received_dict["group_name"])
        queries = [query_delete,query_update_hosts]
        
    db.apply(queries)
    
# Função que pega a configuração de grupo recebida via socket e processa no DB
def process_recv_hosts(received_dict):

    db  = DB_daemon("database/hosts_groups.db", received_dict)
    queries = []
    if received_dict["action"] == "insert" or received_dict["action"] == "update":
        
        # Loop para criação de query para atualizar o grupo associado a um endereço
        for host in received_dict["targets"]:
            query = "update openwrt set group_name = \"{}\" where address = \"{}\";".format(received_dict["group_name"],host)
            queries.append(query)
        
    elif received_dict["action"] == "delete":
        
        # Loop para criação de queries para remover hosts de um grupo, colocando eles no Default
        for host in received_dict["targets"]:
            query_update_hosts = "update openwrt set group_name = \"{}\" where address = \"{}\";".format("Default",host)
            queries.append(query_update_hosts)
        
    db.apply(queries)
    

# Função que pega a os parâmetros para listagem de hosts e usa para fazer busca no DB
def process_recv_hosts_list(received_dict):

    # Instancia objeto de queries com o banco de dados
    db  = DB_daemon("database/hosts_groups.db", received_dict)
    
    # Verifica se a listagem de hosts tem o parâmetro all
    if received_dict["params"]["group_name"] == "all":
        query = "select * from openwrt;"
    # Caso contrário construa a query de acordo com o grupo do nome.
    # Não é necessário verificar a existência, na API norte já é feita a verificação.
    else:
        query = "select * from openwrt where group_name = \"{}\";".format(received_dict["params"]["group_name"])
    
    # Executa a query definida acima    
    result = db.apply_select_host(query)    
    
    # Retorna o resultado da query
    return result

# Função que pega os parâmetros de listagem para uma determinada configuração e usa para fazer busca no DB
def process_recv_config_list(received_dict, initial_query):

    # Pega o nome de todos os parâmetros enviados como filtros
    params_keys = list(received_dict["params"].keys())
    
    # Array para armazenar as configurações que não são all
    not_all = []
    # Loop para verificar se existem configurações que não são all
    for param in params_keys:
        if received_dict["params"][param] == "all":
            pass
        else:
            # Se não for all coloca no array
            not_all.append(param)
            
    # Se todos forem all não há necessidade de adicionar filtros no select
    if len(not_all) == 0:
        query = initial_query+";"
        
    # Se houver um único que não é all coloque como filtro
    else:
        final_query = " where "
        iterator = 0
        for key in not_all:
            if iterator == len(not_all)-1:
                string = "\"{}\"=\"{}\";".format(key,received_dict["params"][key])
            else:
                string = "\"{}\"=\"{}\" AND ".format(key,received_dict["params"][key])
            
            final_query += string
            
            iterator += 1
        
        query = initial_query+final_query
    
    print("final query: {}".format(query))
    
    conn = sqlite3.connect("database/configs.db")
    cursor = conn.cursor()
    
    # Executa a query
    cursor.execute(query)
    # Pega os resultados da query
    results = cursor.fetchall()
    
    return results

# Função que retorna o resultado da listagem para a northboundAPI
def send_result_list_loop(result,conn):
    iterator = 0
    # Loop para retorno dos resultados para NorthboundAPI
    while iterator <= len(result):
        if iterator == len(result):
            # Envia o sinalizador para encerrar o socket do outro lado
            send_data = json.dumps({"Status":"End"}).encode('utf-8')
        else:
            send_data = json.dumps(result[iterator]).encode('utf-8')
                        
        # Envia o resultado da listagem para northbound interface
        conn.sendall(send_data)
        time.sleep(0.01)
                            
        iterator += 1
        
def pre_send_list_result(received_dict,initial_query,conn,sub_config):
    # Realiza o processamento da listagem de configuração
    results = process_recv_config_list(received_dict, initial_query)
                                    
    # Se não houver resultados para o filtro aplicado retorne a mensagem abaixo
    if len(results) == 0:
        send_result_list_loop([{"Response":"No such configurations found in the database: {}".format(received_dict)}],conn)
    
    send_result = []
    # Loop de confecção de dicionários para resposta da requisição bem estruturada
    for result in results:
        possible_configs = ["ipv4","dhcp","dhcp_static","dhcp_relay","RIP","QoS","DNS","fw"]
        if sub_config == "dhcp":
            dict_result = {"Interface":result[2],"Start":result[3],"Limit DHCP":result[4],"Lease Time":result[5],"Group":result[6],"OpenWRT":result[7]}
            
        elif sub_config == "dhcp_static":
            dict_result = {"MAC":result[2],"IP":result[3],"Group":result[4],"OpenWRT":result[5]}
            
        elif sub_config == "dhcp_relay":
            dict_result = {"ID_Relay":result[2],"Interface":result[3],"Local_ADDR":result[4],"Server_ADDR":result[5],"Group":result[6],"OpenWRT":result[7]}

        elif sub_config == "ipv4":
            dict_result = {"Address":result[2],"Netmask":result[3],"Gateway":result[4],"DNS":result[5],"Group":result[6],"OpenWRT":result[7]}
            
        elif sub_config == "rip":
            dict_result = {"Interface":result[2],"Target":result[3],"Netmask":result[4],"Gateway":result[5],"Group":result[6],"OpenWRT":result[7]}

        elif sub_config == "qos":
            dict_result = {"Interface":result[2],"Enabled":result[3],"Class group":result[4],"Overhead":result[5],"Download":result[6],"Upload":result[7],"Group":result[8],"OpenWRT":result[9]}

        elif sub_config == "dns":
            dict_result = {"Address":result[2],"Group":result[3],"OpenWRT":result[4]}

        elif sub_config == "iptables":
            # TODO
            #dict_result = {"Interface":result[2],"Start":result[3],"Limit DHCP":result[4],"Lease Time":result[5]}
            dict_result = {"None":"None"}
            pass
            
        send_result.append(dict_result)

    # Função de envio dos resultados para northbound interface
    send_result_list_loop(send_result,conn)

# Função que inicializa o socket para receber configs da northbound API
def db_daemon_recv():
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Inicializando o socket
        s.bind((HOST,PORT))
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
                    
                    if received_dict["global"] == "config":
                        # Realiza o processamento da configuraçaõ
                        process_recv_configs(received_dict)
                        break
                    elif received_dict["global"] == "group":
                        # Realiza o processamento da configuração de grupo
                        process_recv_groups(received_dict)
                        break
                        
                    elif received_dict["global"] == "host":
                        # Realiza o processamento da configuração de hosts
                        process_recv_hosts(received_dict)
                        break
                    
                    elif received_dict["global"] == "config_list":
                        # Processamento de listagem para config list
                        if received_dict["sub_config"] == "dhcp":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from dhcp"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"dhcp")
                            
                        elif received_dict["sub_config"] == "dhcp_static":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from dhcp_static"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"dhcp_static")
                            
                        elif received_dict["sub_config"] == "iptables":
                            # TODO definir parâmetros para regras de iptables para voltar aqui
                            # Define o inicio da query para listagem
                            # initial_query = "select * from fw"
                            
                            # pre_send_list_result(received_dict,initial_query,conn,"iptables")
                            pass
                            
                        elif received_dict["sub_config"] == "dhcp_relay":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from dhcp_relay"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"dhcp_relay")
                            
                        elif received_dict["sub_config"] == "ipv4":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from ipv4"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"ipv4")
                            
                        elif received_dict["sub_config"] == "rip":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from RIP"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"rip")
                            
                        elif received_dict["sub_config"] == "qos":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from QoS"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"qos")
                            
                        elif received_dict["sub_config"] == "dns":
                            
                            # Define o inicio da query para listagem
                            initial_query = "select * from DNS"
                            
                            pre_send_list_result(received_dict,initial_query,conn,"dns")
                            
                        break
                    
                    elif received_dict["global"] == "host_list":
                        # Realiza o processa da listagem de hosts
                        result = process_recv_hosts_list(received_dict)
                        
                        # Função de envio dos resultados para northbound interface
                        send_result_list_loop(result,conn)

                        break
                    
                except json.decoder.JSONDecodeError as err:
                    pass
                
                # # Realiza o processamento da configuraçaõ
                # process_recv_configs(received_dict)
                # break
            
                # Finalizando a conexão
            conn.close()

            

# Função que realiza o envio de configurações para a southbound API
def db_daemon_send(config_json,SEND_HOST,SEND_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
        s.connect((SEND_HOST, SEND_PORT)) # conecta ao servidor da southbound API
        send_data = json.dumps(config_json).encode('utf-8')
        s.sendall(send_data) # manda a mensagem
        s.close()

if __name__ == "__main__":
    
    #db = DB_daemon("a", rule_dict)
    #result = db.create_query_config()
    #print(result)
    # Fazer a escuta e envio por fork
    db_daemon_recv()
    
    