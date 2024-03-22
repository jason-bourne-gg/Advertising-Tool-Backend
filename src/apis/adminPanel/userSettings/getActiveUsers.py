from flask import Blueprint, jsonify,session
import logging
from flask_login import login_required 
from models import UserDetails
from util.decorators import update_user_activity


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

active_users_blueprint = Blueprint('users', __name__)

active_users_store = {}

@active_users_blueprint.route('/getactiveusers', methods=['GET'])
@login_required
@update_user_activity
def getActiveUsers():
    data_obj_list = UserDetails.query.all()
    data = []
    for user_obj in data_obj_list :
        # print(user_obj.id, user_obj.name, user_obj.email)
        dict={}
        dict["id"]=user_obj.id
        dict["name"]=user_obj.name
        dict["email"]=user_obj.email
        dict["role"]=user_obj.role
        dict["access_granter"]=user_obj.access_granter
        dict["access_granted_on"]=user_obj.access_granted_on
        # # print(dict)
        data.append(dict)
        # print(data)
    response = {}
    response['data'] = data
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    #logger.debug(response)
    return response 
 
    