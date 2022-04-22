from flask import Flask, request, jsonify, redirect, url_for
import northutils
import socket
import json

############################### FLASK API - PATHs ##########################################
        
app = Flask(__name__)

# INFO do socket db_daemon (recebimento de configs)
HOST = "127.0.0.1"
PORT = 65001

## Path for testing
@app.route("/hi")
def hi():
    return "<p>Hello</p>"

## Force HTTPS connections to the API
@app.before_request
def before_request():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)


# API path to generate the JWT Token based on the passed data
@app.route("/admin/token", methods=['POST'])
def jwt_token():
    
    post_data = request.get_json(force=True)
    
    # TODO - Algum procedimento para validação do ADMIN
    
    # Reads the private key file for JWT token creation
    priv_key = northutils.get_key("./keys/northbound.key")
    jwt_token = jwt.encode(post_data, priv_key, algorithm="RS256")
    
    jwt_token_json = jsonify({"JWT":jwt_token})
    
    return jwt_token_json
    

# API path used for listing the managed OpenWRT gateways
@app.route("/device/list", methods=['POST'])
def device_list():
    
    post_data = request.get_json(force=True)
    
    # Get's the JWT field from the JSON
    jwt_token = post_data["JWT"]
    
    # Reads the public key file for JWT decoding
    pub_key = northutils.get_key("./keys/northbound.key.pub")
    
    # Attempts JWT decoding
    jwt_decoded = northutils.attempt_jwt_decode(jwt_token, pub_key)

    if jwt_decoded[0]:
        print(jwt_decoded[1])
        return "<p>Success</p>"
    else:
        response_dict = {"ERROR":"JWT - "+jwt_decoded[1]}
        return jsonify(response_dict)        

# API para o recebimento de regras de configuração dos OpenWRT
@app.route("/admin/config", methods=['POST'])
def config():
    
    # Pega o conteúdo enviado pelo POST
    post_data = request.get_json(force=True)
    
    # Reads the public key file for JWT decoding
    pub_key = northutils.get_key("./keys/northbound.key.pub")
    
    # Attempts JWT decoding
    jwt_token = post_data["JWT"]
    jwt_decoded = northutils.attempt_jwt_decode(jwt_token, pub_key)

    # Se não deu nenhum erro na decodificação    
    if jwt_decoded[0]:
        
        # Cria o objeto para configuração
        sent_config = northutils.Config(post_data)
        
        # Verifica se a configuração é válida
        if sent_config.check_parameters_rule(known_parameters_json):

            config_array = []
            # Loop para criação de uma config para cada ip abordado na regra
            for target_name in post_data["targets"].keys():
                for ip in post_data["targets"][target_name]:
                    rule_dict = {"action":post_data["action"],
                                 "JWT":post_data["JWT"],
                                 "who":post_data["who"],
                                 "timestamp":post_data["timestamp"],
                                 "type":post_data["type"],
                                 "fields":post_data["fields"],
                                 "targets":{target_name:[ip]},
                                 "schedule":post_data["schedule"]
                                 }
                    
                    # Insere a assinatura única da regra no corpo da mesma
                    rule_dict = northutils.hash_rule(rule_dict)
                    
                    # Insere a configuração no array
                    config_array.append(rule_dict)

            # Array para regras nao duplicadas
            success_rule = []
            # Array para regras duplicadas
            duplicate_rule = []
            # Loop para verificação individual de cada hashs
            for config in config_array:
                # Verifica se a regra já foi cadastrada por comparação de hash
                if config["rule_hash"] not in hash_array:                    
                    # Coloca a regra em uma lista de sucesso
                    success_rule.append(config)
                        
                    # Adiciona o hash de uma regra criada no hash em memória
                    hash_array.append(config["rule_hash"])
                
                else:
                    # Coloca os endereços que já possuem essa regra em duplicate_rule
                    duplicate_rule.append(config["targets"])
            
            # Se não houverem duplicatas
            if len(duplicate_rule) == 0:
                
                # Envia as configurações não duplicadas
                sent_config.send(success_rule)
                
                # Retorna mensagem de sucesso
                return jsonify({"SUCCESS":"The rules have been received and are not duplicates."})
            
            else:
                
                # Envia as configurações não duplicadas
                sent_config.send(success_rule)
                
                # Retorna mensagem de sucesso
                return jsonify({"ERROR":"The rule is a duplicate of previously existing rule. - The rule is a duplicate for the following targets: {}".format(duplicate_rule),
                                "INFO":"If there were any other targets in your config they have been received and saved."})
        else:
            return jsonify({"ERROR":"Invalid fields or parameters sent."})
        
    else:
        response_dict = {"ERROR":"JWT - "+jwt_decoded[1]}

# Função principal da API northbound
def northbound_main():
    global hash_array
    hash_array = []
    
    # Deixar em memórias os parâmetros das configurações
    global known_parameters_json
    known_parameters_json = northutils.load_all_possible_parameters()
    
    # Carrega o hash de todas as regras cadastradas
    global configured_hash_array
    configured_hash_array = northutils.load_all_applied_configs()
    
    for hashe in configured_hash_array:
        hash_name = hashe[0]
        hash_array.append(hash_name)
    
    # Flask webApp configuration - running on SSL
    app.run(debug=True,host="0.0.0.0",port=8080, ssl_context=('./keys/northbound.crt','./keys/northbound.key'))

if __name__ == "__main__":
    # Inicializa a API northbound
    northbound_main()