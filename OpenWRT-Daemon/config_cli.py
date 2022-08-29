import sqlite3
import daemon_utils

# Atualiza a configuração do daemon
def update_config(address,netmask,port):
    
    # Pega a porta do dispositivo gerenciado
    conn = sqlite3.connect("database/host_config.db")
    cursor = conn.cursor()
    # Atualiza o registro do host
    cursor.execute("update host set address = \"{}\", netmask = \"{}\", port = \"{}\" where id = 1;".format(address,
                                                                                                            netmask,
                                                                                                            port))
    
    conn.commit()
    conn.close()

# Atualiza a configuração do controller
def update_config_controller(address,netmask,port):
    
    # Pega a porta do dispositivo gerenciado
    conn = sqlite3.connect("database/controller_config.db")
    cursor = conn.cursor()
    # Atualiza o registro do host
    cursor.execute("update controller set address = \"{}\", netmask = \"{}\", port = \"{}\" where id = 1;".format(address,
                                                                                                            netmask,
                                                                                                            port))
    
    conn.commit()
    conn.close()

# Função principal 
def main():

    # Pega as configurações atuais do daemon
    config = daemon_utils.startup_process()
    
    # Mostra as informações atuais do daemon
    print("INFO - Current host config: {}".format(config))
    
    answer = "a"
    # Loop para verificação de config
    while answer != "y" and answer != "n":
        answer = input("Do you want to change the OpenWRT Daemon configuration? [y/n] ")
        
    if answer == "y":

        # Pega as configurações de endereços IPV4, porta e netmask
        print("WARN - Be sure to check that the configs are the correct IP, port and netmask you want")
        address = input("New address (current: {}) = ".format(config["address"]))
        port = input("New port (current: {}) = ".format(config["port"]))
        port = int(port)
        netmask = input("New netmask (current: {}) = ".format(config["netmask"]))
        
        update_config(address, netmask, port)
        print("INFO - Daemon config updated successfully\n")
        
        controller_config = daemon_utils.controller_config()
        print("INFO - Current controller config: {}".format(controller_config))
        
        while answer != "y" and answer != "n":
            answer = input("Do you want to change the Controller configuration? [y/n] ")
        
        if answer == "y":
            
            # Pega as configurações de endereços IPV4, porta e netmask
            print("WARN - Be sure to check that the configs are the correct IP, port and netmask you want")
            address = input("New address (current: {}) = ".format(controller_config["address"]))
            port = input("New port (current: {}) = ".format(controller_config["port"]))
            port = int(port)
            netmask = input("New netmask (current: {}) = ".format(controller_config["netmask"]))
        
            update_config_controller(address, netmask, port)
            print("INFO - Daemon config updated successfully\n")
            
        else:
            pass
    
    else:
        
        controller_config = daemon_utils.controller_config()
        print("INFO - Current controller config: {}".format(controller_config))
        
        while answer != "y" and answer != "n":
            answer = input("Do you want to change the Controller configuration? [y/n] ")
        
        if answer == "y":
            
            # Pega as configurações de endereços IPV4, porta e netmask
            print("WARN - Be sure to check that the configs are the correct IP, port and netmask you want")
            address = input("New address (current: {}) = ".format(controller_config["address"]))
            port = input("New port (current: {}) = ".format(controller_config["port"]))
            port = int(port)
            netmask = input("New netmask (current: {}) = ".format(controller_config["netmask"]))
        
            update_config_controller(address, netmask, port)
            print("INFO - Daemon config updated successfully\n")
            
        else:
            pass

if __name__ == "__main__":
    
    main()