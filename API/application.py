from flask import Flask, request, jsonify
from jsonschema import validate
import os, json, jwt
from pymongo import MongoClient
from bson.json_util import dumps
from bson import ObjectId
from datetime import datetime, timezone, timedelta
from functools import wraps
from bcrypt import hashpw, checkpw, gensalt

TOKEN_SECRET = 'TFG'

try:
    client:MongoClient = MongoClient('mongodb://localhost:27017/')
    db = client.smite2
    # Prueba la conexión
    db.command("ping")
    print("Conexión exitosa a MongoDB")
except Exception as e:
    print(f"Error al conectar a MongoDB: {e}")

path_base:str = os.path.dirname(os.path.abspath(__file__))
application = Flask(__name__)

@application.route("/", methods=['GET'])
def running():
    return "<h1>SMITE 2</h1>"

# METHODS GET

# METHODS OF GODS
@application.route("/gods", methods=['GET'])
def get_gods():
    filter:dict = {}
    projection:dict = {
        '_id': 1,
        'name': 1,
        'pantheon': 1,
    }
    try: 
        gods:list = list(db.gods.find(filter, projection))
    except Exception as e:
        print(str(e))
    return jsonify(json.loads(dumps(gods))), 200
    
@application.route("/gods/<string:id>", methods=['GET']) # objectId of god
def get_god(id:str):
    if not ObjectId.is_valid(id):
        return errorId()
    
    filter:dict = {
        '_id': ObjectId(id)
    }
    projection:dict = {
    }
    
    try:
        god:dict = db.gods.find_one(filter, projection)
    except Exception as e:
        print(str(e))
    
    return jsonify(json.loads(dumps(god))), 200

# Filters of gods

# Rol
@application.route("/gods_rol/<string:rol>", methods=['GET'])
def get_gods_rol(rol:str):
    roles:list = ['Mid', 'Support', 'Solo', 'Carry', 'Jungle']
    rol = rol.capitalize()
    
    if rol not in roles:
        return notExist()
    
    filter:dict = {
        'rol': rol
    }
    projection:dict = {
        '_id': 1,
        'name': 1,
        'pantheon': 1,
        'rol': 1,
    }

    gods:list = list(db.gods.find(filter, projection))
    return jsonify(json.loads(dumps(gods)))

# Pantheon
@application.route("/gods_pantheon/<string:pantheon>", methods=['GET'])
def get_gods_pantheon(pantheon:str):
    pantheons:list = ['Arabia', 'Arthurian', 'Celtic', 'Chinese', 'Egyptian', 'Hindu', 'Japanese', 'Korean', 'Maya', 'Polynesian', 'Roman', 'Voodoo', 'Yoruba' 'Greek', 'Norse']
    pantheon = pantheon.capitalize()

    if pantheon not in pantheons:
        return notExist()
    
    filter:dict = {
        'pantheon': pantheon.capitalize()
    }
    projection:dict = {
        '_id': 1,
        'name': 1,
        'pantheon': 1,
    }

    gods:list = list(db.gods.find(filter, projection))
    return jsonify(json.loads(dumps(gods)))

# Type
@application.route("/gods_type/<string:type>", methods=['GET'])
def get_gods_type(type:str):
    types:list = ['Physical', 'Magical']
    type = type.capitalize()

    if type not in types:
        return notExist()
    filter:dict = {
        'type': type.capitalize()
    }
    projection:dict = {
        '_id': 1,
        'name': 1,
        'pantheon': 1,
        'type': 1
    }

    gods:list = list(db.gods.find(filter, projection))
    return jsonify(json.loads(dumps(gods)))

# Methods of abilities
@application.route("/ability/<string:id>", methods=['GET']) # objetitId of ability
def get_ability(id:str):
    if not ObjectId.is_valid(id):
        return errorId()
    filter:dict = {
        '_id': ObjectId(id)
    }
    projection:dict = {}

    ability:dict = db.abilities.find_one(filter, projection)
    return jsonify(json.loads(dumps(ability)))

# Abilities of one god
@application.route("/abilities_of_god/<string:id>", methods=['GET']) # objectiveId of god
def get_abilities_of_god(id:str):
    if not ObjectId.is_valid(id):
        return errorId()
    filter:dict = {
        '_id': ObjectId(id)
    }
    projection:dict = {
        '_id': 1,
        'name': 1,
        'abilities': 1
    }
    god:dict = db.gods.find_one(filter, projection)
    
    if not god:
        return notExist()
    
    ids_abilities:list[str] = god['abilities']
    abilities:list = []
    for id in ids_abilities:
        filter = {
            '_id': ObjectId(id)
        }
        ability:dict = db.abilities.find_one(filter)
        abilities.append(ability)
    return jsonify(json.loads(dumps(abilities))), 200


# Filters of abilities
@application.route("/abilities/<string:type>")
def get_ability_type(type:str):
    types:list = ['BASIC' 'PASSIVE' 'ABILITY 1', 'ABILITY 2', 'ABILITY 3', 'ULTIMATE']
    type = type.upper()
    if type not in types:
        return notExist()
    filter:dict = {
        'type': type
    }
    projection:dict = {}
    abilities:list = list(db.abilities.find(filter, projection)) 
    return jsonify(json.loads(dumps(abilities)))

@application.route("/insert_god_in_user/<string:id_user>/<string:id_god>", methods=['POST'])
def insert_god_in_user(id_user:str, id_god:str):
    if not ObjectId.is_valid(id_user) or not ObjectId.is_valid(id_god):
        return errorId()
    filter:dict = {
        '_id': ObjectId(id_user)
    }
    user:dict = db.users.find_one(filter)
    filter:dict = {
        '_id': ObjectId(id_god)
    }
    god:dict = db.gods.find_one(filter)
    if not user or not god:
        return notExist()
    gods:list = user['gods']
    gods.append(ObjectId(id_god))
    filter = {
        '_id': ObjectId(id_user)
    }
    update_user:dict = {
        '$set': {'gods': gods}
    }
    result:dict = db.users.update_one(filter, update_user)
    if result:
        return jsonify({'Update': 'God inserted correctly'})
    else: 
        return jsonify({'Error': 'Error'})
    
def errorId() -> jsonify:
    return jsonify({'Error':'Invalid ID'})

def notExist() -> jsonify:
    return jsonify({'Error': 'Not exist'})

def get_schema(name:str) -> dict:
    with open(f'{path_base}/{name}.json', 'r', encoding='utf8') as fd:
        return json.loads(fd.read())

# USERS

# REGISTER
@application.route("/register", methods=['POST'])
def register():
    try:
        data:dict = request.get_json()
        if not data:
            return jsonify({'Error': 'There is no data'})
        
        schema:dict = get_schema('user_schema')
        validate(instance=data, schema=schema)
    except Exception as e:
        print(str(e))
        return jsonify({'Error': 'Invalid Data'})
    password = data['password'].encode('utf-8')
    hashed_password = hashpw(password, gensalt())
    gods:list = []
    user_data:dict = {
        'username': data['username'],
        'email': data['email'],
        'password': hashed_password.decode('utf8'),
        'gods': gods
    }
    result = db.users.insert_one(user_data)
    if not result.inserted_id:
        return jsonify({'Error': 'Ocurrio un error'}), 400
    else:
        return jsonify({'id': str(result.inserted_id)}), 201
    
        
@application.route("/login", methods=['POST'])
def login():
    try:
        data:dict = request.get_json()
        email:str = data.get('email')
        password:str = data.get('password')

        if not data:
            return jsonify({'Error': 'Empty data'})
        
        filter:dict = {
            'email': email
        }
        projection:dict = {}

        user:dict = db.users.find_one(filter, projection)
        if not user:
            return jsonify({'Error': 'User not exists'})
        
        password_bytes = password.encode('utf-8')
        stored_hash = user['password'].encode('utf-8')

        if checkpw(password_bytes, stored_hash):
            token_data:dict = {
                '_id': str(user['_id']),
                'username': user['email'],
                'exp': datetime.now(timezone.utc) + timedelta(minutes=60)
            }
            token:str = jwt.encode(token_data, TOKEN_SECRET, algorithm="HS256")
            return jsonify({'token': token}), 200
        else:
            return jsonify({"Error": "Incorrect Password"}), 400
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Error'}), 400


if __name__ == '__main__':
    application.run(debug=True)