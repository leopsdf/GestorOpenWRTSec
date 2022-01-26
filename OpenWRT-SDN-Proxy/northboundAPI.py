from flask import Flask, request, jsonify, redirect, url_for
import jwt


########################### Utility functions used on the API paths ##############################


# Reads the key file and returns it's contents in byte format, ready to be used for SSL or JWT token encoding
def get_key(file_name):
    key =""
    with open(str(file_name), 'rb') as file:
        key = file.read()
        file.close()
        
    return key


# Return array - [0] true if decoded successfully or false if error, [1] decoded jwt if true or error message if false
def attempt_jwt_decode(jwt_token, pub_key):
    try:
        decoded_jwt_token = jwt.decode(jwt_token, pub_key, algorithms="RS256")
        return [True, decoded_jwt_token]
    except jwt.exceptions.InvalidTokenError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    except jwt.exceptions.DecodeError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    except jwt.exceptions.InvalidSignatureError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]
    except jwt.exceptions.ExpiredSignatureError as err:
        err = jsonify({"ERROR":"JWT - "+str(err)})
        return [False, err]


############################### FLASK API - PATHs ##########################################
        
app = Flask(__name__)

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
    priv_key = get_key("./keys/northbound.key")
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
    pub_key = get_key("./keys/northbound.key.pub")
    
    # Attempts JWT decoding
    jwt_decoded = attempt_jwt_decode(jwt_token, pub_key)

    if jwt_decoded[0]:
        print(jwt_decoded[1])
        return "<p>Success</p>"
    else:
        response_dict = {"ERROR":"JWT - "+jwt_decoded[1]}
        return jsonify(response_dict)        
    
        

if __name__ == "__main__":
    
    # Flask webApp configuration - running on SSL
    app.run(debug=True,host="0.0.0.0",port=8080, ssl_context=('./keys/northbound.crt','./keys/northbound.key'))
