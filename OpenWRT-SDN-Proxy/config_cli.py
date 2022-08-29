import sqlite3
import southutils
import db_daemon
import northutils


# Atualiza a configuração do controller
def update_config_controller(north_dict, southAPI_dict, southSocket_dict, db_dict):

    # Se conecta ao banco de dados
    conn = sqlite3.connect("database/controller.db")
    cursor = conn.cursor()
    # Atualiza os registros
    cursor.execute("update northboundAPI set address = \"{}\", port = \"{}\" where id = 1;".format(north_dict["address"],
                                                                                                    north_dict["port"]))
    
    cursor.execute("update southboundAPI set address = \"{}\", port = \"{}\" where id = 1;".format(southAPI_dict["address"],
                                                                                                    southAPI_dict["port"]))
    
    cursor.execute("update southbound_socket set address = \"{}\", port = \"{}\" where id = 1;".format(southSocket_dict["address"],
                                                                                                    southSocket_dict["port"]))
    
    cursor.execute("update db set address = \"{}\", port = \"{}\" where id = 1;".format(db_dict["address"],
                                                                                        db_dict["port"]))
    
    conn.commit()
    conn.close()

# Função principal 
def main():

    # Pega as configurações de todas as entidades do controller
    northAPI_config = northutils.startup_north()
    south_config = southutils.startup_south()
    southAPI_config = south_config[0]
    southSocket_config = south_config[1]
    db_config = db_daemon.startup_db()
    
    # Mostra as informações atuais do daemon
    print("INFO - Current host config")
    print("northboundAPI - {}".format(northAPI_config))
    print("southboundAPI - {}".format(southAPI_config))
    print("southSocket   - {}".format(southSocket_config))
    print("db_config     - {}".format(db_config))
    
    answer = "a"
    # Loop para verificação de config
    while answer != "y" and answer != "n":
        answer = input("Do you want to change the controller configuration? [y/n] ")
        
    if answer == "y":

        # Pega as configurações de endereços IPV4, porta e netmask para cada entidade
        print("WARN - Be sure to check that the configs are the correct IP and port you want\n")
        
        print("### NorthboundAPI")
        north_address = input("New address (current: {}) = ".format(northAPI_config["address"]))
        north_port = input("New port (current: {}) = ".format(northAPI_config["port"]))
        north_port = int(north_port)
        
        north_dict = {"address":north_address,
                      "port":north_port}
        
        print("\n### SouthboundAPI")
        south_address = input("New address (current: {}) = ".format(southAPI_config["address"]))
        south_port = input("New port (current: {}) = ".format(southAPI_config["port"]))
        south_port = int(south_port)
        
        southAPI_dict = {"address":south_address,
                      "port":south_port}
        
        print("\n### SouthSocket")
        south_address = input("New address (current: {}) = ".format(southSocket_config["address"]))
        south_port = input("New port (current: {}) = ".format(southSocket_config["port"]))
        south_port = int(south_port)
        
        southSocket_dict = {"address":south_address,
                      "port":south_port}
        
        print("\n### db_daemon")
        db_address = input("New address (current: {}) = ".format(db_config["address"]))
        db_port = input("New port (current: {}) = ".format(db_config["port"]))
        db_port = int(db_port)
        
        db_dict = {"address":db_address,
                      "port":db_port}
        
        
        update_config_controller(north_dict, southAPI_dict, southSocket_dict, db_dict)
        print("\nINFO - Configuration applied in the database")

    else:
        pass

if __name__ == "__main__":
    
    main()