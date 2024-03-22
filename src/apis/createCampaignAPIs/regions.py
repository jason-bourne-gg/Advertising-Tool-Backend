from flask import Blueprint, jsonify,session,Response
import logging
from flask_login import login_required 
from models import Region,user_region,UserDetails
from database import db


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

region_blueprint = Blueprint('region', __name__)

region_store = {}

@region_blueprint.route('/getallregions', methods=['GET'])
@login_required
def getAllRegions():
    data_obj_list = Region.query.all()
    data = []
    for region_obj in data_obj_list :
        # print(brand_obj.id, brand_obj.brand_code, brand_obj.brand_name)
        dict={}
        dict["id"]=region_obj.id
        dict["code"]=region_obj.region_code
        dict["name"]=region_obj.region_name
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
 






@region_blueprint.route('/getuserregions', methods=['GET'])
@login_required
def get_user_regions():
    # Get the user's email from the session
    session_user_email = session["okta_attributes"].get('email')

    if not session_user_email:
        message = "You do not have access to 'Nautilus' application. Please contact the owner of the application for access."
        print(message)
        return Response(response=message, status=601)

    # Query the user's ID
    user_id = UserDetails.query.filter_by(email=session_user_email).with_entities(UserDetails.id).scalar()

    if user_id is None:
        message = "You do not have access to 'Nautilus' application. Please contact the owner of the application for access."
        print(message)
        return Response(response=message, status=601)

    # print(session_user_email, user_id)

    # Query the region IDs associated with the user
    region_ids = db.session.query(user_region.c.region_id).filter(user_region.c.user_id == user_id).all()
    region_ids = [region_id[0] for region_id in region_ids]
    # print(region_ids)

    # Query the region objects based on region IDs
    region_objs = Region.query.filter(Region.id.in_(region_ids)).all()
    # print(region_objs)

    # Create a list of dictionaries containing region information
    data = [{"id": region_obj.id, "code": region_obj.region_code, "name": region_obj.region_name} for region_obj in region_objs]

    response = {
        'data': data,
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
    }

    return response
