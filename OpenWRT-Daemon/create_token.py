import string
import hashlib
import sqlite3
import random
import daemon_utils
import requests
import json

# TODO QUANDO CRIAR UM NOVO TOKEN COM HOST JÁ AUTH É NECESSÁRIO REALIZAR UM DEAUTH E DELETAR TODAS AS REGRAS ASSOCIADAS

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
    conn = sqlite3.connect("database/host_config.db")
    cursor = conn.cursor()
    # Atualiza o registro do host
    cursor.execute("update host set token = \"{}\" where id = 1;".format(token))
    cursor.execute("update host set token_status = 1 where id = 1;")
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    
    inputa = "a"
    while inputa != "y" and inputa != "n":
        inputa = input("Do you want to generate a new token? (WARN - if token was already generated and openwrt is authenticated in the controller this process can create a mismatch in the database)[y/n]? ")
    
    if inputa == "y":
        startup_config = daemon_utils.startup_process()
        
        # Verifica se já existe um token
        if startup_config["token_status"] == 0:
        
            token = create()
            print("INFO - New generated token: {}".format(token))
            update_token(token)
            print("INFO - Token successfully updated.")    
            
        else:
            # Se já existir inicia o processo de /switch na southboundAPI
            old_token = startup_config["token"]
            
            # Cria um novo token
            token = create()
            print("INFO - New generated token: {}".format(token))
            
            # Pega as configurações do controller
            controller_config = daemon_utils.controller_config()
            
            # Prepara o payload
            switch_payload = {"new_token":token,
                              "token":old_token}
            
            try:
                requested = requests.post("http://{}:{}/switch".format(controller_config["address"],controller_config["port"]), json=switch_payload)
                
                response = json.loads(requested.text)
                print(response)
                
                if response["STATUS"] == "ERROR":
                    print("ERROR - Couldnt switch token.")
                
                else:
                    print("INFO - Switch Success")
                    
                    # Insere um novo token no db
                    update_token(token)
                    print("INFO - Token successfully updated.")

            
            except requests.HTTPError as err:
                print(err)
            except requests.ConnectionError as err:
                print(err)
            except requests.Timeout as err:
                print(err)
            except requests.ConnectTimeout as err:
                print(err)
            
    else:
        pass