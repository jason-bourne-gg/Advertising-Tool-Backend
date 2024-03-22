from flask import Blueprint, jsonify,session
import logging
from flask_login import login_required 
from models import Brand,user_brand,UserDetails
from database import db


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

brand_blueprint = Blueprint('brand', __name__)

brand_store = {}

def getBrandName (name):
    if '|' in name:
        # Split the string by the "|" character and get the first part
        name_before_pipe = name.split("|")[0]
        return name_before_pipe
    else:
        # Return the original string if "|" is not found
        return name


@brand_blueprint.route('/getallbrands', methods=['GET'])
@login_required
def getAllBrands():
    data_obj_list = Brand.query.all()
    data = []
    for brand_obj in data_obj_list :
        # print(brand_obj.id, brand_obj.brand_code, brand_obj.brand_name)
        dict={}
        dict["id"]=brand_obj.id
        dict["code"]=brand_obj.brand_code
        dict["name"]=getBrandName(brand_obj.brand_name)
        # print(dict)
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
 



@brand_blueprint.route('/getuserbrands', methods=['GET'])
@login_required
def getUserBrands():

    # session_user_email = "deba@sigmoidanalytics.com"
    session_user_email = session["okta_attributes"]['email']
    session_user_id_tuple = UserDetails.query.with_entities(UserDetails.id).filter_by(email=session_user_email).first() #returns a tuple
    print(session_user_email,session_user_id_tuple[0])


    # brand_id_list = user_brand.query.with_entities(user_brand.user_id).filter_by(user_id = session_user_id[0]).all() .........this query dosent work on relationship tables
    brand_ids_tuple = db.session.query(user_brand.c.brand_id).filter(user_brand.c.user_id == session_user_id_tuple[0]).all()
    print(brand_ids_tuple)

    brand_ids = [brand_id[0] for brand_id in brand_ids_tuple ] 
    print(brand_ids)
    data = []

    brand_objs = Brand.query.filter(Brand.id.in_(brand_ids)).all()
    print(brand_objs)

    for brand_obj in brand_objs :
        # print(brand_obj.id, brand_obj.brand_code, brand_obj.brand_name)
        dict={}
        dict["id"]=brand_obj.id
        dict["code"]=brand_obj.brand_code
        dict["name"]=getBrandName(brand_obj.brand_name)
        # print(dict)
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