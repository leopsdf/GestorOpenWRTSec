import daemon_utils
import create_token
import requests

def deauth():
    
    # Pega configuração do daemon
    startup_config = daemon_utils.startup_process()
    
    # Pega configuração do controller
    controller_config = daemon_utils.controller_config()
    
    # Payload de desautenticação
    deauth_payload = {"token":startup_config["token"],"address":startup_config["address"]}
    
    # Envia o request de desautenticação
    requested = requests.post("http://{}:{}/deauth".format(controller_config["address"],controller_config["port"]), json=deauth_payload)
    
    
if __name__ == "__main__":
    
    deauth()