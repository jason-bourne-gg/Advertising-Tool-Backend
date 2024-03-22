import datetime
import logging
from flask import Blueprint, jsonify, session, request, make_response
from flask_login import login_required 
from models import Campaign
from database import db
from datetime import datetime, time
from sqlalchemy import update
import json
from util.decorators import update_user_activity

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

expiredcampaigns_blueprint = Blueprint('expiredcampaigns', __name__)


@expiredcampaigns_blueprint.route('/getallexpiredcampaigns', methods=['GET'])
@login_required
@update_user_activity
def getallexpiredCampaigns():
    try:
        data_obj_list = Campaign.query.filter_by(campaign_status = "EXPIRED").all()
        data = []

        for item_obj in data_obj_list:
            dict = {}

            dict["id"] = item_obj.id
            dict["name"] = item_obj.campaign_name
            dict["created_by"] = item_obj.user_details.name
            dict["created_by_email"] = item_obj.created_by_email
            dict["created_on"] = item_obj.created_on
            dict["last_modified_on"] = item_obj.modified_on
            dict["started_on"] = item_obj.start_time
            dict["ended_on"] = item_obj.end_time
            dict["order_id"] = item_obj.order_id

            data.append(dict)

        response = {}
        response['data'] = data
        response["status"] = {
            "statusMessage": "Success",
            "statusCode" : 200
        }
        return response  
    

    except Exception as e:
        response = {}
        response["data"] = {}
        status = {
                    "statusCode": 500,
                    "statusMessage": "Could Not Retrieve Expired Campaigns", 
                    "error": str(e)
                  }
        response["status"] = status

        logger.debug(response)
        return response, 500    
    # logger.debug(response)
    

@expiredcampaigns_blueprint.route('/deleteexpiredcampaign', methods=['DELETE'])
@login_required
@update_user_activity
def deleteexpiredCamapign():

    data = request.json

    try:
        # Check if the entry already exists in the database based on the 'id'
        existing_expired_campaign = Campaign.query.filter_by(order_id=data['order_id']).first()

        if existing_expired_campaign:
            # If the entry exists, delete the entry frome the campaign_drafts table
            db.session.delete(existing_expired_campaign) #Need to add code to CASCADE DELETE
            db.session.commit()

        else:
            response = {
                "status": {
                    "statusMessage": "Could not find the requested Expired campaign.",
                    "statusCode": 500
                }
            }
            logger.debug(response)
            return response, 500

    except Exception as e:
        response = {}
        status = {"statusCode": 500,
                  "statusMessage": "Internal Server Error", "error": str(e)}
        response["status"] = status
        
        db.session.rollback()  # Rollback the transaction if an exception occurs
        logger.debug(response)
        return response, 500


    response = {
            "message": {"message": "Expired Campaign has been deleted successfully."},
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
    return response



@expiredcampaigns_blueprint.route('/getDetailsofexpiredCampaign', methods=['POST'])
@login_required
@update_user_activity
def getDetailsOfExpiredCampaign():

    # camp_id = request.args.get("id")
    request_data = request.json
    camp_id = request_data['id']
    print(camp_id)

    dict = {}
    try:
        # Check if the entry exists in the database based on the 'id' column
        item_obj = Campaign.query.filter_by(id=camp_id).first()
        
        if item_obj:
            dict["id"] = item_obj.id
            dict["campaignName"] = item_obj.campaign_name
            dict["created_by"] = item_obj.user_details.name
            dict["created_by_email"] = item_obj.created_by_email
            dict["created_on"] = item_obj.created_on
            dict["last_modified_on"] = item_obj.modified_on
            dict["brand"] = item_obj.brand.brand_name
            dict["region"] = item_obj.region.region_name
            dict["goal"] = item_obj.goal_goal_kpi.goal_name
            dict["goalKPI"] = item_obj.goal_kpi
            dict["contexts"] = item_obj.context_list
            dict["product_tracking_list"] = item_obj.product_tracking_list
            dict["startDate"] = item_obj.start_time
            dict["endDate"] = item_obj.end_time
            dict["audienceIds"] = item_obj.audience_ids
            dict["totalBudget"] = item_obj.total_budget
            dict["maxChangeInBudget"] = item_obj.max_change_in_budget
            dict["campaign_status"] = item_obj.campaign_status
            dict["orderPONumber"] = item_obj.orderPO_number
            dict["domainNames"] = item_obj.domain_names
            dict["suggestion"] = item_obj.suggestions
        
        else:
            response = {
                "status": {
                    "statusMessage": "Could not find the requested expired campaign.",
                    "statusCode": 500
                }
            }
            logger.debug(response)
            return response, 500

    except Exception as e:
        response = {}
        response["data"] = {}
        status = {"statusCode": 500,
                  "statusMessage": "Error Fetching Details of Requested Expired Camapign (INTERNAL SERVER ERROR)", "error": str(e)}
        response["status"] = status

        logger.debug(response)
        return response, 500

    response = {}
    response['data'] = dict
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    return response   