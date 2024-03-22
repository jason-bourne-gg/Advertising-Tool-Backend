from flask import request, jsonify, Blueprint,session
import requests
from database import db 
from models import Brand,Region,TargetPlatform,CampaignType  
import logging
from flask_login import login_required 
from settings.config import okta_org_url, okta_client_id

okta_org_url = 'https://rb.okta.com/'
okta_client_id = '0oazwj6u9l29pdWut0x7'

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

smallapis_blueprint = Blueprint('smallapis', __name__)

smallapis_store = {}

@smallapis_blueprint.route('/addnewbrand', methods=['POST'])
@login_required
def addNewBrand():
    try:
        request_data = request.json
        brand_name = request_data['brandName']

        newBrand = Brand (brand_name = brand_name.upper())
        db.session.add(newBrand)
        db.session.commit()

        response = {}
        response['messsage'] = f"NEW BRAND '{brand_name.upper()}' ADDED TO DATABASE"
        status = {
            "statusMessage": "Success",
            "statusCode": 200
        }
        response['status'] = status
        return response

    except Exception as e:
        logging.error(e)
        response = {"data": {}}
        status = {"statusCode": 500,
                  "statusMessage": "Error in adding Brand to DB", "error": str(e)}
        response["status"] = status

        return response



@smallapis_blueprint.route('/addnewregion', methods=['POST'])
@login_required
def addNewRegion():
    try:
        request_data = request.json
        region_name = request_data['regionName']

        newRegion = Region (region_name = region_name.upper())
        db.session.add(newRegion)
        db.session.commit()

        response = {}
        response['messsage'] = f"New Region '{region_name.upper()}' added to Database"
        status = {
            "statusMessage": "Success",
            "statusCode": 200
        }
        response['status'] = status
        return response

    except Exception as e:
        logging.error(e)
        response = {"data": {}}
        status = {"statusCode": 500,
                  "statusMessage": "Error in adding region to DB", "error": str(e)}
        response["status"] = status

        return response



@smallapis_blueprint.route('/getallplatformsandcampaigntypes', methods=['GET'])
@login_required
def getallPlatforms():
    try:
        data = []
        platformobjs = TargetPlatform.query.all()
        for obj in platformobjs:
            dict ={}
            dict['platform_name'] = obj.platform
            dict['id'] = obj.id

            campaigntype_objs = CampaignType.query.filter_by(target_platform_id = obj.id ).all()
            camp_obj_array = []
            for obj in campaigntype_objs:
                camp_obj_dict ={}
                camp_obj_dict['campaign_type_name'] = obj.campaign_type
                camp_obj_dict['id'] = obj.id
                camp_obj_array.append(camp_obj_dict)

            dict['campaign_types'] = camp_obj_array
            data.append(dict)

        response = {}
        response ['data'] = data
        status = {
            "statusMessage": "Success",
            "statusCode": 200
        }
        response['status'] = status
        return response

    except Exception as e:
        logging.error(e)
        response = {"data": {}}
        status = {"statusCode": 500,
                  "statusMessage": "Error in getting platforms from DB", "error": str(e)}
        response["status"] = status

        return response    
    


