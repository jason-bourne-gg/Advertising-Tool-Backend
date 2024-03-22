from flask import request, jsonify, Blueprint,session
import requests
from database import db 
from models import UserDetails  
import logging
from flask_login import login_required 
from settings.config import okta_org_url, okta_client_id, reckitt_okta_api_token
import os

env = os.environ.get("ENV")
if env == 'dev' :
    okta_org_url = 'https://rb.okta.com/'
    okta_client_id = '0oazwj6u9l29pdWut0x7'

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

oktausers_blueprint = Blueprint('oktausers', __name__)

brand_store = {}

api_token = reckitt_okta_api_token

def search_okta_users(search_query):

    users_endpoint = f'{okta_org_url}/api/v1/apps/{okta_client_id}/users?q={search_query}'

    # Set the headers with the API token
    headers = {
        'Authorization': f'SSWS {api_token}',
        'Accept': 'application/json'
    }

    # Send the GET request to retrieve the list of application users with search
    response = requests.get(users_endpoint, headers=headers)
    users = response.json()
    response = []
    # print("Users:", users)
    # Process the user data
    for user in users:
        user_id = user['id']
        user_email = user['profile']['email']
        user_name = user['profile']['name']
        user_object = {
            "email":user_email,
            "name":user_name
        }
        response.append(user_object)

    return response


@oktausers_blueprint.route('/searchoktausersofreckitt', methods=['POST'])
@login_required
def getOktaUSersOfReckitt():

    try:
        search_query = request.json["searchString"]
        print("search_query: ", search_query)
        user_list = search_okta_users(search_query)
        response = {}
        status = {
            "statusMessage": "Success",
            "statusCode": 200
        }
        response["status"] = status
        response["data"] = user_list

        return response

    except Exception as ex:
        logging.error(ex)
        response = {"data": {}}
        status = {"statusCode": 500,
                  "statusMessage": "Internal Server Error", "error": str(ex)}
        response["status"] = status

        return response
 





@oktausers_blueprint.route('/addoktausertodb', methods=['POST'])
@login_required
def addOktaUserToDB():
    request_data = request.json
    email_to_add = request_data['email']
    user_name = request_data ['name']

    try:
        # Check if the user with the same email already exists in your database
        existing_user = UserDetails.query.filter_by(email=email_to_add).first()

        if not existing_user:
            # If the user does not exist in the database, add it
            new_user = UserDetails(email=email_to_add, name = user_name, access_granter = session["okta_attributes"]['given_name'], role= 'user')
            db.session.add(new_user)
            db.session.commit()
            return jsonify({'message': 'User added to the database successfully', 
                            "status" : {
                                "statusMessage": "Success",
                                "statusCode": 200
                            }})
        else:
            return jsonify({'message': 'User already exists in the database'})

    except Exception as ex:
        logging.error(ex)
        response = {"data": {}}
        status = {"statusCode": 500,
                  "statusMessage": "Internal Server Error", "error": str(ex)}
        response["status"] = status

        return response
    



@oktausers_blueprint.route('/deletektauserfromdb', methods=['DELETE'])
@login_required
def deleteOktaUserfromDB():
    request_data = request.json
    email_to_delete = request_data['email']
    user_name = request_data ['name']

    try:
        # Check if the user with the same email already exists in your database
        existing_user = UserDetails.query.filter_by(email=email_to_delete).first()

        if existing_user:
            # If the user does not exist in the database, add it
            user_to_delete = existing_user
            db.session.delete(user_to_delete)
            db.session.commit()
            return jsonify({'message': 'User Deleted to the database successfully', 
                            "status" : {
                                "statusMessage": "Success",
                                "statusCode": 200
                            }})
        else:
            return jsonify({'message': 'User does not exists in the database'})

    except Exception as ex:
        logging.error(ex)
        response = {"data": {}}
        status = {"statusCode": 500,
                  "statusMessage": "Internal Server Error", "error": str(ex)}
        response["status"] = status

        return response    