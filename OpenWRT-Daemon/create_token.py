import string
import hashlib
import sqlite3
import random

# TODO QUANDO CRIAR UM NOVO TOKEN COM HOST JÁ AUTH É NECESSÁRIO REALIZAR UM DEAUTH E DELETAR TODAS AS REGRAS ASSOCIADAS

# Cria o token utilizado na autenticação
def create_token():
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
    
    conn.commit()
    conn.close()
    
if __name__ == "__main__":
    
    inputa = "a"
    while inputa != "y" and inputa != "n":
        inputa = input("Do you want to generate a new token? (WARN - if token was already generated and openwrt is authenticated in the controller this process can create a mismatch in the database)[y/n]? ")
    
    if inputa == "y":
        token = create_token()
        print("INFO - New generated token: {}".format(token))
        update_token(token)
        print("INFO - Token successfully updated.")    
    else:
        pass