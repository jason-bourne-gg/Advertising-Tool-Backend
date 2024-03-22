import os
from models import UserDetails
from flask import Blueprint, jsonify,session
import logging
from flask_login import login_required , UserMixin
from util.decorators import update_user_activity

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)



user_blueprint = Blueprint('user', __name__)

user_store = {}



@user_blueprint.route('/userinfo', methods=['GET','PUT'])
@update_user_activity
@login_required
def get_user():
    response = {}
    logger.info("/userinfo GET API called")
    # Session contains the user name and email
    print(session['okta_attributes'])
    user_name = session['okta_attributes']['given_name']
    user_email = session['okta_attributes']['email']
    
    db_user = UserDetails.query.filter_by(email = user_email).first()
    
    response['data'] = {"name": user_name,
                        "email": user_email,
                        "role":db_user.role}
    response["status"] = {
        "statusMessage": "Success"
    }
    logger.debug(response)
    return response

    




class User(UserMixin):
    def __init__(self, user_id):
        user = {}
        self.id = None
        self.name = None
        self.email = None
        try:
            user = user_store[user_id]
            print('----------')
            print(user)
            self.id = user_id
            self.name = user['name']
            self.email = user['email']
        except:
            pass


