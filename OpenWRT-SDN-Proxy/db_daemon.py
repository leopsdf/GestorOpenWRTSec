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

# INFO do socket db_daemon (recebimento de configs)
HOST = "127.0.0.1"
PORT = 65001

# INFO envio de configs para southbound
HOST_SOUTH = "127.0.0.1"
PORT_SOUTH = 65002

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
            cursor.execute(query)

        # Salva as mudanças feitas
        conn.commit()
        conn.close()

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
    # Verifica se a regra é para configuração de OpenWRT
    if received_dict["type"] != "group":
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
                
    # Verifica se a regra é para criação de grupos lógicos
    else:
        print("placeholder - criação de grupo")

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
                except json.decoder.JSONDecodeError as err:
                    pass
                # Realiza o processamento da configuraçaõ
                process_recv_configs(received_dict)
                break
            
                # Finalizando a conexão
            conn.close()

            

# Função que realiza o envio de configurações para a southbound API
def db_daemon_send(config_json):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # cria o obj socket | AF_INET p/ IPv4 | SOCK_STREAM -> p/ TCP
        s.connect((HOST_SOUTH, PORT_SOUTH)) # conecta ao servidor da southbound API
        send_data = json.dumps(config_json).encode('utf-8')
        s.sendall(send_data) # manda a mensagem

if __name__ == "__main__":
    
    #db = DB_daemon("a", rule_dict)
    #result = db.create_query_config()
    #print(result)
    # Fazer a escuta e envio por fork
    db_daemon_recv()
    
    