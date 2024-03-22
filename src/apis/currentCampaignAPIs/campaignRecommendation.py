from flask import Blueprint, jsonify,session,request,make_response,Response
import datetime
import logging
from flask_login import login_required 
import requests
import json
from json import JSONDecodeError
from models import CampaignRecommendations
from database import db
from datetime import datetime
from settings.functions import *
from sqlalchemy import or_

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

campaignrecommendations_blueprint = Blueprint('campaignrecommendations', __name__)

brand_store = {}

@campaignrecommendations_blueprint.route('/getcampaignrecommendations', methods=['POST'])
@login_required
def pendingCampaignRecommendation(): 
    request_data = request.json
    # print(request_data)
    try:
        reco_objs = CampaignRecommendations.query.filter_by(order_id=request_data["order_id"], status="PENDING").all()
        print("reco_objs", reco_objs)
    except JSONDecodeError as e:
        logging.error("JSON decoding error: %s", str(e))
        return Response(f"JSON decoding error: {str(e)}", 500)    
    
    data =[]
    
    for reco_obj in reco_objs:
        dict ={}
        dict["recommendation_text"]  = reco_obj.recommendation_text
        dict["status"] = reco_obj.status
        dict["line_item_id"] = reco_obj.line_item_id
        dict["generation_date"] = reco_obj.date_of_generation
        dict['recommendation_obj'] = reco_obj.recommendation_object
        dict['id'] = reco_obj.id
        # dict['recommendation_obj'] = json.loads(reco_obj.recommendation_object)
        data.append(dict)
        # print(dict)



    response = {
            "data": data,
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
        
    return response






@campaignrecommendations_blueprint.route('/getpastcampaignrecommendations', methods=['POST'])
@login_required
def expiredCampaignRecommendation():
    request_data = request.json
    # print(request_data)
    # reco_objs = CampaignRecommendations.query.filter_by(order_id= request_data["order_id"]).filter(or_( status = "APPROVED", status = "DENIED")).all()
    recommendation_objs = CampaignRecommendations.query.filter_by(order_id=request_data["order_id"]).filter(or_(CampaignRecommendations.status == 'APPROVED', CampaignRecommendations.status == 'DENIED')).all()
    print(recommendation_objs)
    data =[]
    
    for recommendation_obj in recommendation_objs:
        dict ={}
        dict["recommendation_text"]  = recommendation_obj.recommendation_text
        dict["status"] = recommendation_obj.status
        dict["line_item_id"] = recommendation_obj.line_item_id
        dict["generation_date"] = recommendation_obj.date_of_generation
        dict["date_of_user_action"] = recommendation_obj.date_of_user_action
        dict['recommendation_obj'] = recommendation_obj.recommendation_object
        dict['id'] = recommendation_obj.id
        # dict['recommendation_obj'] = json.loads(reco_obj.recommendation_object)
        data.append(dict)
        # print (dict)

    response = {
            "data": data,
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
        
    return response