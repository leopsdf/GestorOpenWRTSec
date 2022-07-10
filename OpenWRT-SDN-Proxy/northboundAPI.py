from flask import Flask, request, jsonify, redirect, url_for
import northutils
import socket
import json

############################### FLASK API - PATHs ##########################################
        
app = Flask(__name__)

# INFO do socket db_daemon (recebimento de configs)
HOST = "127.0.0.1"
PORT = 65001

known_groups = []
known_host_group_relation = {}

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

######################### APIs de listagem #############################

@app.route("/admin/list/host/", defaults={'group_name':'all'},methods=['GET'])
@app.route("/admin/list/host/<group_name>",methods=['GET'])
def list_by_group(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "host_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"group_name":"all"}
        pass
    # Caso contrário utilize o nome do grupo passado como argumento
    else:
        # Seleciona todos os grupos cadastrados na ferramenta
        known_groups = northutils.load_all_groups()
        # Verifica se o nome do grupo usado como filtro existe
        if group_name not in known_groups:
            # Se não existir retorna mensagem de erro
            return jsonify({"ERROR":"Group name '{}' is not a known group.".format(group_name)})
        
        # Parâmetros enviados para requisição ao banco de dados
        params = {"group_name":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params)
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})
    
    
########################################################################



# API para criação de novos grupos
@app.route("/admin/group",methods=['POST'])
def group():
    # Pega o conteúdo enviado pelo POST
    post_data = request.get_json(force=True)
    
    # Reads the public key file for JWT decoding
    pub_key = northutils.get_key("./keys/northbound.key.pub")
    
    # Attempts JWT decoding
    jwt_token = post_data["JWT"]
    jwt_decoded = northutils.attempt_jwt_decode(jwt_token, pub_key)
    
    # Se não deu nenhum erro na decodificação    
    if jwt_decoded[0]:
    
        sent_config = northutils.Config(post_data)

        # Carrega os grupos conhecidos
        known_groups = northutils.load_all_groups()
        
        # Verifica se a configuração está correta.
        if sent_config.check_group(known_groups):
            # Se um grupo for criado coloque o nome do mesmo no objeto em memória known_groups
            # if post_data["action"] == "create":
            #     known_groups.append(post_data["group_name"])
            #     print(known_groups)
            #     return jsonify({"OK":"OK"})
            # # Se um grupo for removido remova o nome do mesmo do objeto em memória known_groups
            # elif post_data["action"] == "delete":
            #     known_groups = [x for x in known_groups if x != post_data["group_name"]]
            #     print(known_groups)
            #     return jsonify({"OK":"OK"})
            
            # Insere a tag de group para do db_daemon
            post_data["global"] = "group"
            
            # Envia a configuração para o db_daemon
            sent_config.send([post_data])
            
            return jsonify({"SUCCESS":"The group configuration has been received."})
            
        else:
            return jsonify({"ERROR":"Invalid fields or parameters sent."})
    
    else:
        response_dict = {"ERROR":"JWT - "+jwt_decoded[1]}
        return jsonify(response_dict)
    
# API para criação de novos grupos
@app.route("/admin/host",methods=['POST'])
def host():
    # Pega o conteúdo enviado pelo POST
    post_data = request.get_json(force=True)
    
    # Reads the public key file for JWT decoding
    pub_key = northutils.get_key("./keys/northbound.key.pub")
    
    # Attempts JWT decoding
    jwt_token = post_data["JWT"]
    jwt_decoded = northutils.attempt_jwt_decode(jwt_token, pub_key)
    
    # Se não deu nenhum erro na decodificação    
    if jwt_decoded[0]:
    
        sent_config = northutils.Config(post_data)

        # Carrega os grupos conhecidos
        known_groups = northutils.load_all_groups()
        # Carrega as relações entre hosts e grupos
        known_host_group_relation = northutils.load_host_group_relation(known_groups)
        # Carrega os hosts conhecidos
        known_hosts = northutils.load_all_hosts()
        
        # Verifica se a configuração está correta.
        if sent_config.check_host(known_hosts, known_groups, known_host_group_relation):
            # Se um grupo for criado coloque o nome do mesmo no objeto em memória known_groups
            # if post_data["action"] == "create":
            #     known_groups.append(post_data["group_name"])
            #     print(known_groups)
            #     return jsonify({"OK":"OK"})
            # # Se um grupo for removido remova o nome do mesmo do objeto em memória known_groups
            # elif post_data["action"] == "delete":
            #     known_groups = [x for x in known_groups if x != post_data["group_name"]]
            #     print(known_groups)
            #     return jsonify({"OK":"OK"})
            
            # Insere a tag de group para do db_daemon
            post_data["global"] = "host"
            
            # Envia a configuração para o db_daemon
            sent_config.send([post_data])
            
            return jsonify({"SUCCESS":"The host configuration has been received successfully."})
            
        else:
            return jsonify({"ERROR":"Invalid fields or parameters sent.",
                            "INFO":"Check if all the required parameters were sent. Observe if the targets and the groups exist in the database."})
    
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
                    # Verifica se a ação é delete para não dar problemas com assinaturas
                    if post_data["action"] == "delete":
                        rule_dict = {"action":"apply",
                                    "JWT":post_data["JWT"],
                                    "who":post_data["who"],
                                    "timestamp":post_data["timestamp"],
                                    "type":post_data["type"],
                                    "fields":post_data["fields"],
                                    "targets":{target_name:[ip]},
                                    "schedule":post_data["schedule"]
                                    }
                        
                    else:
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
                    
                    # Retorna a ação para delete
                    if post_data["action"] == "delete":
                        rule_dict["action"] = "delete"
                        
                    # Insere a tag de group para do db_daemon
                    rule_dict["global"] = "config"
                        
                    # Insere a configuração no array
                    config_array.append(rule_dict)

            # Array para regras nao duplicadas
            success_rule = []
            # Array para regras duplicadas
            duplicate_rule = []
            # Loop para verificação individual de cada hashs
            for config in config_array:
                
                hash_array = []
                configured_hash_array = northutils.load_all_applied_configs()
                for hashe in configured_hash_array:
                    hash_name = hashe[0]
                    hash_array.append(hash_name)
                
                if config["action"] == "delete":
                    success_rule.append(config)
                else:
                    # Verifica se a regra já foi cadastrada por comparação de hash
                    if config["rule_hash"] not in hash_array:                    
                        # Coloca a regra em uma lista de sucesso
                        success_rule.append(config)
                            
                        # Adiciona o hash de uma regra criada no hash em memória
                        #hash_array.append(config["rule_hash"])
                    
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
        return jsonify(response_dict)

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