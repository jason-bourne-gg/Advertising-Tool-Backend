import datetime
import logging
from flask import Blueprint, jsonify, session, request, make_response
from flask_login import login_required 
from models import CampaignDrafts
from database import db
from datetime import datetime, time
from sqlalchemy import update
from util.decorators import update_user_activity


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

savedraft_blueprint = Blueprint('savedraft', __name__)


@savedraft_blueprint.route('/getallsaveddrafts', methods=['GET'])
@login_required
@update_user_activity
def getallsaveddrafts():

    data_obj_list = CampaignDrafts.query.all()
    data = []

    for item_obj in data_obj_list:
        dict = {}

        dict["id"] = item_obj.id
        dict["name"] = item_obj.campaign_name
        dict["created_by"] = item_obj.user_details.name
        dict["created_by_email"] = item_obj.created_by_email
        dict["created_on"] = item_obj.created_on
        dict["last_modified_on"] = item_obj.modified_on

        data.append(dict)

    response = {}
    response['data'] = data
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    # logger.debug(response)
    return response  

@savedraft_blueprint.route('/editdraft', methods=['GET'])
@login_required
@update_user_activity
def editdraft():

    camp_id = request.args.get("id")

    dict = {}
    try:
        # Check if the entry exists in the database based on the 'id' column
        item_obj = CampaignDrafts.query.filter_by(id=camp_id).first()
        
        if item_obj:
            dict["id"] = item_obj.id
            dict["campaignName"] = item_obj.campaign_name
            dict["created_by"] = item_obj.user_details.name
            dict["created_by_email"] = item_obj.created_by_email
            dict["created_on"] = item_obj.created_on
            dict["last_modified_on"] = item_obj.modified_on
            dict["brand"] = item_obj.brand
            dict["region"] = item_obj.region
            dict["goal"] = item_obj.goal
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
            dict["suggestion"] = item_obj.suggestion
            dict["domainNames"] = item_obj.domain_names
        
        else:
            response = {
                "status": {
                    "statusMessage": "Could not find the requested campaign draft.",
                    "statusCode": 500
                }
            }
            logger.debug(response)
            return response, 500

    except Exception as e:
        response = {}
        response["data"] = {}
        status = {"statusCode": 500,
                  "statusMessage": "Internal Server Error", "error": str(e)}
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

@savedraft_blueprint.route('/savecampaignasdraft', methods=['POST'])
@login_required
def savecampaignasdraft():

    data = request.json
    
    date_format = "%Y-%m-%d"
    created_by_email = session["okta_attributes"]['email']
    created_on = datetime.utcnow()
    modified_on = datetime.utcnow()

    try:
        # Check if the entry already exists in the database based on the 'campaign_name'
        existing_campaign = CampaignDrafts.query.filter_by(campaign_name=data['campaignName']).first()

        if existing_campaign:
            # If the entry exists, update the table based on new values
            query = update(CampaignDrafts)\
                        .where(CampaignDrafts.campaign_name == data['campaignName']) \
                        .values({CampaignDrafts.brand : data['brand'], \
                                CampaignDrafts.region : data["region"], \
                                CampaignDrafts.goal : data["goal"],  \
                                CampaignDrafts.goal_kpi : data['goalKPI'],  \
                                CampaignDrafts.context_list : data['contexts'],  \
                                CampaignDrafts.product_tracking_list : data['product_tracking_list'],  \
                                CampaignDrafts.start_time :datetime.strptime(data['startDate'], date_format),    \
                                CampaignDrafts.end_time : datetime.strptime(data['endDate'], date_format), \
                                CampaignDrafts.audience_ids : data['audienceIds'],   \
                                CampaignDrafts.total_budget : data['totalBudget'],       \
                                CampaignDrafts.max_change_in_budget : data['maxChangeInBudget'],  \
                                CampaignDrafts.created_by_email : created_by_email,  \
                                CampaignDrafts.modified_on : modified_on,       \
                                CampaignDrafts.orderPO_number : data['orderPONumber'],    \
                                CampaignDrafts.domain_names : data['domainNames'], \
                                CampaignDrafts.suggestion : data['suggestion']})
            
            db.session.execute(query)
            db.session.commit()
            
        else:
            # If the entry does not exist, create a new row in the table
            draft_camp = CampaignDrafts(
                                        campaign_name = data['campaignName'],
                                        brand = data['brand'],
                                        region = data["region"],
                                        goal = data["goal"],
                                        goal_kpi = data['goalKPI'],
                                        context_list = data['contexts'],
                                        product_tracking_list = data['product_tracking_list'],
                                        start_time = datetime.strptime(data['startDate'], date_format),  
                                        end_time = datetime.strptime(data['endDate'], date_format), 
                                        audience_ids = data['audienceIds'],
                                        total_budget = data['totalBudget'],
                                        max_change_in_budget = data['maxChangeInBudget'],
                                        campaign_status = "DRAFT",
                                        created_by_email = created_by_email,
                                        created_on = created_on,
                                        modified_on = modified_on,
                                        orderPO_number = data['orderPONumber'],
                                        domain_names = data['domainNames'],
                                        suggestion = data['suggestion']
                                        )
            db.session.add(draft_camp)
            db.session.commit()

    except Exception as e:
        # raise ("Error!! Could not save campaign draft into Database: " + str(e), 500) 
    
        response = {}
        status = {"statusCode": 500,
                  "statusMessage": "Internal Server Error", "error": str(e)}
        response["status"] = status

        logger.debug(response)
        return response, 500

    response = {
            "message": {"message": "Campaign draft has been saved successfully."},
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
    return response

@savedraft_blueprint.route('/deletedraft', methods=['DELETE'])
@update_user_activity
@login_required
def deletedraft():

    data = request.json

    try:
        # Check if the entry already exists in the database based on the 'id'
        existing_draft = CampaignDrafts.query.filter_by(id=data['id']).first()

        if existing_draft:
            # If the entry exists, delete the entry frome the campaign_drafts table
            db.session.delete(existing_draft)
            db.session.commit()

        else:
            response = {
                "status": {
                    "statusMessage": "Could not find the requested campaign draft.",
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

        logger.debug(response)
        return response, 500


    response = {
            "message": {"message": "Campaign draft has been deleted successfully."},
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
    return response