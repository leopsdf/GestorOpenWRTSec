from flask import Flask, request, jsonify, redirect, url_for
import northutils
import socket
import json
import re
import configparser

############################### FLASK API - PATHs ##########################################
        
app = Flask(__name__)

known_groups = []
known_host_group_relation = {}

## Force HTTPS connections to the API
# @app.before_request
# def before_request():
#     if not request.is_secure:
#         url = request.url.replace('http://', 'https://', 1)
#         code = 301
#         return redirect(url, code=code)


# API path to generate the JWT Token based on th0e passed data
@app.route("/admin/token", methods=['POST'])
def jwt_token():
    
    post_data = request.get_json(force=True)
    
    # TODO - Algum procedimento para validação do ADMIN
    
    # Reads the private key file for JWT token creation
    priv_key = northutils.get_key("./keys/northbound.key")
    jwt_token = jwt.encode(post_data, priv_key, algorithm="RS256")
    
    jwt_token_json = jsonify({"JWT":jwt_token})
    
    return jwt_token_json

######################### APIs de listagem de host por parâmetros#############################

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
    result = northutils.send_list_query_to_db(query_type, params,None)
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})


######################### APIs de listagem de grupos lógicos#############################

@app.route("/admin/list/group",methods=['GET'])
def list_group():
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "group_list"
    # Se não for passado o nome do grupo selecione todos
    params = {"group_name":"all"}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,None)
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})



######################### APIs de listagem de configuração por grupo ################################

@app.route("/admin/list/config/dhcp/group", defaults={'group_name':'all'})
@app.route("/admin/list/config/dhcp/group/<group_name>")
def list_by_group_dhcp(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dhcp")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

@app.route("/admin/list/config/dhcp_relay/group", defaults={'dhcp_relay':'all'})
@app.route("/admin/list/config/dhcp_relay/group/<group_name>")
def list_by_group_dhcp_relay(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dhcp_relay")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

@app.route("/admin/list/config/ipv4/group", defaults={'ipv4':'all'})
@app.route("/admin/list/config/ipv4/group/<group_name>")
def list_by_group_ipv4(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"ipv4")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

@app.route("/admin/list/config/qos/group", defaults={'qos':'all'})
@app.route("/admin/list/config/qos/group/<group_name>")
def list_by_group_qos(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"qos")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})


@app.route("/admin/list/config/rip/group", defaults={'rip':'all'})
@app.route("/admin/list/config/rip/group/<group_name>")
def list_by_group_rip(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"rip")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

@app.route("/admin/list/config/dns/group", defaults={'dns':'all'})
@app.route("/admin/list/config/dns/group/<group_name>")
def list_by_group_dns(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dns")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

@app.route("/admin/list/config/dhcp_static/group", defaults={'dhcp_static':'all'})
@app.route("/admin/list/config/dhcp_static/group/<group_name>")
def list_by_group_dhcp_static(group_name):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    # Se não for passado o nome do grupo selecione todos
    if group_name == "all":
        params = {"logical_group":"all"}
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
        params = {"logical_group":group_name}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dhcp_static")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

######################### APIs de listagem de config por parâmetros#############################

# dhcp
@app.route("/admin/list/config/dhcp", defaults={'interface':'all','start':'all','limit_dhcp':'all','leasetime':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp/<interface>", defaults={'start':'all','limit_dhcp':'all','leasetime':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp/<interface>/<start>", defaults={'limit_dhcp':'all','leasetime':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp/<interface>/<start>/<limit_dhcp>", defaults={'leasetime':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp/<interface>/<start>/<limit_dhcp>/<leasetime>", methods=['GET'])
def list_config_dhcp(interface,start,limit_dhcp,leasetime):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    
    # Verifica se os tipos dos parâmetros passados estão corretos
    if interface != "all":
        if type(interface) != str:
            return jsonify({"ERROR":"Interface name '{}' is not a string.".format(interface)})
        
    if start != "all":
        # Verifica se o valor passado em start pode ser um inteiro
        try:
            new_start = int(start)
        except ValueError as err:
            return jsonify({"ERROR":"Start ip '{}' is not a integer.".format(start)})
        
    if limit_dhcp != "all":
        # Verifica se o valor passado em limit_dhcp pode ser um inteiro
        try:
            new_limit = int(limit_dhcp)
        except ValueError as err:
            return jsonify({"ERROR":"limit_dhcp '{}' is not a number.".format(limit_dhcp)})
    
    # Verifica todas as condições para que o lease_time seja do tipo número+h
    if leasetime != "all":
        if type(leasetime) != str:
            return jsonify({"ERROR":"leasetime '{}' is not a string.".format(leasetime)})
        else:
            if len(leasetime) <= 1 or len(leasetime) > 3:
                return jsonify({"ERROR":"leasetime '{}' must be of length 1-3 characters containg number+h.".format(leasetime)})
            
            elif leasetime[len(leasetime)-1] != 'h':
                return jsonify({"ERROR":"leasetime '{}' last character must be an 'h' (hour).".format(leasetime)})
                
            else:
                without_h = leasetime.replace("h","")
                for character in without_h:
                    try:
                        temp = int(character)
                    except ValueError as err:
                        return jsonify({"ERROR":"leasetime '{}' must be number followed by an 'h'. E.g: 12h".format(leasetime)})
        
    # Parâmetros enviados para requisição ao banco de dados
    params = {"interface":interface,'start':start,'limit_dhcp':limit_dhcp,'leasetime':leasetime}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dhcp")
        
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

# dhcp_static
@app.route("/admin/list/config/dhcp_static", defaults={'mac':'all','ip':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp_static/<mac>", defaults={'ip':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp_static/<mac>/<ip>",methods=['GET'])
def list_config_dhcp_static(mac,ip):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"

    if mac != "all":
        # Verifica se não é um mac válido
        if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", mac.lower()):
            return jsonify({"ERROR":"MAC '{}' is not a valid address.".format(mac)})
    
    if ip != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(ip)
        except socket.error:
            return jsonify({"ERROR":"IP '{}' is not a valid address.".format(ip)})
    
    # Parâmetros enviados para requisição ao banco de dados
    params = {"mac":mac,"ip":ip}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dhcp_static")
    
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})
    
# iptables
# TODO

# dhcp_relay
@app.route("/admin/list/config/dhcp_relay", defaults={'id_relay':'all','interface':'all','local_addr':'all','server_addr':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp_relay/<id_relay>", defaults={'interface':'all','local_addr':'all','server_addr':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp_relay/<id_relay>/<interface>", defaults={'local_addr':'all','server_addr':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp_relay/<id_relay>/<interface>/<local_addr>", defaults={'server_addr':'all'},methods=['GET'])
@app.route("/admin/list/config/dhcp_relay/<id_relay>/<interface>/<local_addr>/<server_addr>",methods=['GET'])
def list_config_dhcp_relay(id_relay,interface,local_addr,server_addr):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"

    # Verifica se os tipos dos parâmetros passados estão corretos
    if id_relay != "all":
        if type(id_relay) != str:
            return jsonify({"ERROR":"id_relay '{}' is not a string.".format(id_relay)})
        
    # Verifica se os tipos dos parâmetros passados estão corretos
    if interface != "all":
        if type(interface) != str:
            return jsonify({"ERROR":"Interface name '{}' is not a string.".format(interface)})
        
    if local_addr != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(local_addr)
        except socket.error:
            return jsonify({"ERROR":"local_addr '{}' is not a valid address.".format(local_addr)})
        
    if server_addr != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(server_addr)
        except socket.error:
            return jsonify({"ERROR":"server_addr '{}' is not a valid address.".format(server_addr)})
    
    # Parâmetros enviados para requisição ao banco de dados
    params = {"id_relay":id_relay,"interface":interface,"local_addr":local_addr,"server_addr":server_addr}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dhcp_relay")
    
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

# ipv4
@app.route("/admin/list/config/ipv4", defaults={'ipaddr':'all','netmask':'all','gateway':'all','dns':'all'},methods=['GET'])
@app.route("/admin/list/config/ipv4/<ipaddr>", defaults={'netmask':'all','gateway':'all','dns':'all'},methods=['GET'])
@app.route("/admin/list/config/ipv4/<ipaddr>/<netmask>", defaults={'gateway':'all','dns':'all'},methods=['GET'])
@app.route("/admin/list/config/ipv4/<ipaddr>/<netmask>/<gateway>", defaults={'dns':'all'},methods=['GET'])
@app.route("/admin/list/config/ipv4/<ipaddr>/<netmask>/<gateway>/<dns>",methods=['GET'])
def list_config_ipv4(ipaddr,netmask,gateway,dns):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"

    if ipaddr != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(ipaddr)
        except socket.error:
            return jsonify({"ERROR":"ipaddr '{}' is not a valid address.".format(ipaddr)})
        
    if netmask != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(netmask)
        except socket.error:
            return jsonify({"ERROR":"netmask '{}' is not a valid address.".format(netmask)})
        
    if gateway != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(gateway)
        except socket.error:
            return jsonify({"ERROR":"gateway '{}' is not a valid address.".format(gateway)})
        
    if dns != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(dns)
        except socket.error:
            return jsonify({"ERROR":"dns '{}' is not a valid address.".format(dns)})
    
    # Parâmetros enviados para requisição ao banco de dados
    params = {"ipaddr":ipaddr,"gateway":gateway,"netmask":netmask,"dns":dns}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"ipv4")
    
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

# rip
@app.route("/admin/list/config/rip", defaults={'interface':'all','target':'all','netmask':'all','gateway':'all'},methods=['GET'])
@app.route("/admin/list/config/rip/<interface>", defaults={'target':'all','netmask':'all','gateway':'all'},methods=['GET'])
@app.route("/admin/list/config/rip/<interface>/<target>", defaults={'netmask':'all','gateway':'all'},methods=['GET'])
@app.route("/admin/list/config/rip/<interface>/<target>/<netmask>", defaults={'gateway':'all'},methods=['GET'])
@app.route("/admin/list/config/rip/<interface>/<target>/<netmask>/<gateway>",methods=['GET'])
def list_config_rip(interface,target,netmask,gateway):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    
    # Verifica se os tipos dos parâmetros passados estão corretos
    if interface != "all":
        if type(interface) != str:
            return jsonify({"ERROR":"interface '{}' is not a string.".format(interface)})
        
    # Verifica se os tipos dos parâmetros passados estão corretos
    if target != "all":
        if type(target) != str:
            return jsonify({"ERROR":"target '{}' is not a string.".format(target)})

    if netmask != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(netmask)
        except socket.error:
            return jsonify({"ERROR":"netmask '{}' is not a valid address.".format(netmask)})
        
    if gateway != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(gateway)
        except socket.error:
            return jsonify({"ERROR":"gateway '{}' is not a valid address.".format(gateway)})
    
    # Parâmetros enviados para requisição ao banco de dados
    params = {"interface":interface,"target":target,"netmask":netmask,"gateway":gateway}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"rip")
    
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

# qos
@app.route("/admin/list/config/qos", defaults={'interface':'all','enabled':'all','classgroup':'all','overhead':'all','download':'all','upload':'all'},methods=['GET'])
@app.route("/admin/list/config/qos/<interface>", defaults={'enabled':'all','classgroup':'all','overhead':'all','download':'all','upload':'all'},methods=['GET'])
@app.route("/admin/list/config/qos/<interface>/<enabled>", defaults={'classgroup':'all','overhead':'all','download':'all','upload':'all'},methods=['GET'])
@app.route("/admin/list/config/qos/<interface>/<enabled>/<classgroup>", defaults={'overhead':'all','download':'all','upload':'all'},methods=['GET'])
@app.route("/admin/list/config/qos/<interface>/<enabled>/<classgroup>/<overhead>", defaults={'download':'all','upload':'all'},methods=['GET'])
@app.route("/admin/list/config/qos/<interface>/<enabled>/<classgroup>/<overhead>/<download>", defaults={'upload':'all'},methods=['GET'])
@app.route("/admin/list/config/qos/<interface>/<enabled>/<classgroup>/<overhead>/<download>/<upload>",methods=['GET'])
def list_config_qos(interface,enabled,classgroup,overhead,download,upload):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"

    # Verifica se os tipos dos parâmetros passados estão corretos
    if interface != "all":
        if type(interface) != str:
            return jsonify({"ERROR":"interface '{}' is not a string.".format(interface)})
        
    if enabled != "all":
        # Verifica se o valor passado em enabled pode ser um inteiro
        try:
            new_limit = int(enabled)
        except ValueError as err:
            return jsonify({"ERROR":"enabled '{}' is not a number.".format(enabled)})
        
    # Verifica se os tipos dos parâmetros passados estão corretos
    if classgroup != "all":
        if type(classgroup) != str:
            return jsonify({"ERROR":"classgroup '{}' is not a string.".format(classgroup)})
        
    if overhead != "all":
        # Verifica se o valor passado em enabled pode ser um inteiro
        try:
            new_limit = int(overhead)
        except ValueError as err:
            return jsonify({"ERROR":"overhead '{}' is not a number.".format(overhead)})

    if download != "all":
        # Verifica se o valor passado em enabled pode ser um inteiro
        try:
            new_limit = int(download)
        except ValueError as err:
            return jsonify({"ERROR":"download '{}' is not a number.".format(download)})
        
    if upload != "all":
        # Verifica se o valor passado em enabled pode ser um inteiro
        try:
            new_limit = int(upload)
        except ValueError as err:
            return jsonify({"ERROR":"upload '{}' is not a number.".format(upload)})
    
    # Parâmetros enviados para requisição ao banco de dados
    params = {"interface":interface,"enabled":enabled,"classgroup":classgroup,"overhead":overhead,"download":download,"upload":upload}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"qos")
    
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})

# dns
@app.route("/admin/list/config/dns", defaults={'address':'all'},methods=['GET'])
@app.route("/admin/list/config/dns/<address>", methods=['GET'])
def list_config_dns(address):
    
    # Define o identificador da requisição. Usado pelo db_daemon para saber o que ele está recebendo
    query_type = "config_list"
    
    if address != "all":
        # Verifica se o endereço IP é válido
        try:
            socket.inet_aton(address)
        except socket.error:
            return jsonify({"ERROR":"address '{}' is not a valid IP.".format(address)})
    
    # Parâmetros enviados para requisição ao banco de dados
    params = {"address":address}
    
    # Envia o tipo da query e seus parâmetros para o db_daemon
    result = northutils.send_list_query_to_db(query_type, params,"dns")
    
    # Retorna o resultado para o usuário
    return jsonify({"Status":"Success", "Results":result})
    
################# APIs para configuração de grupos, hosts e configurações ###################################

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
        check_config = sent_config.check_parameters_rule(known_parameters_json)
        if check_config[0]:

            # Carrega os grupos conhecidos
            known_groups = northutils.load_all_groups()
            # Carrega as relações entre hosts e grupos
            known_host_group_relation = northutils.load_host_group_relation(known_groups)
            # Carrega os hosts conhecidos
            known_hosts = northutils.load_all_hosts()


            config_array = []
            # Loop para criação de uma config para cada ip abordado na regra
            for target_name in post_data["targets"].keys():

                # Verifica se o nome do grupo existe
                if target_name not in known_groups:
                    # Se não existir retorna mensagem de erro
                    return jsonify({"ERROR":"Target name '{}' is not a known group.".format(target_name)})
                
                # Verfica se a configuração vai ser aplicada para todos os hosts do grupo
                if post_data["targets"][target_name][0] == "all":
                    ips = known_host_group_relation[target_name]
                
                # Se não for all aplica a configuração para todos os ips passados
                else:
                    ips = post_data["targets"][target_name]
                
                for ip in ips:
                    
                    if ip not in known_hosts:
                        return jsonify({"ERROR":"Host '{}' doesnt exist in the database.".format(ip)})
                    
                    elif ip not in known_host_group_relation[target_name]:
                        return jsonify({"ERROR":"Host '{}' doesnt belong to group {}.".format(ip,target_name)})
                    
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
            return jsonify({"ERROR":"{}".format(check_config[1])})
        
    else:
        response_dict = {"ERROR":"JWT - "+jwt_decoded[1]}
        return jsonify(response_dict)

# Função principal da API northbound
def northbound_main(north_config):
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
    #app.run(debug=True,host="0.0.0.0",port=8080, ssl_context=('./keys/northbound.crt','./keys/northbound.key'))
    #app.run(debug=True,host=north_config["host"],port=north_config["port"])
    app.run(debug=True,host=north_config["address"],port=north_config["port"])

if __name__ == "__main__":
    
    north_config = northutils.startup_north()
    
    northbound_main(north_config)