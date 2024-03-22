from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import Campaign,LineItemMetrics
from sqlalchemy import func, desc
from database import db
from util.decorators import update_user_activity


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

campaign_blueprint = Blueprint('campaign', __name__)

campaign_store = {}

# Assuming you have the models defined as Campaign and UserDetails


@campaign_blueprint.route('/getcampaigns', methods=['GET'])
def getCampaigns():
    campaigns = (
        db.session.query(
            Campaign,
            func.coalesce(func.sum(LineItemMetrics.totalCost), 0).label('total_cost'),
            func.coalesce(
                db.session.query(LineItemMetrics.orderBudget)
                .filter(LineItemMetrics.order_id == Campaign.order_id)
                .order_by(desc(LineItemMetrics.date))
                .limit(1)
                .correlate(Campaign)
                .as_scalar()
            , Campaign.total_budget).label('order_budget')
        )
        .join(LineItemMetrics, Campaign.order_id == LineItemMetrics.order_id, isouter=True)
        .filter(Campaign.campaign_status != "EXPIRED")
        .group_by(Campaign)
        .all()
    )

    data = []
    for campaign, total_cost, order_budget in campaigns:
        budget_remaining = round(order_budget - total_cost, 3)

        dict = {
            "order_id": campaign.order_id,
            "name": campaign.campaign_name,
            "created_by": campaign.user_details.name,
            "total_budget": order_budget,
            "budget_remaining": budget_remaining,
            "created_on": campaign.created_on,
            "last_modified_on": campaign.modified_on,
            "brand": campaign.brand.brand_name,
            "region": campaign.region.region_name,
            "campaign_status": campaign.campaign_status,
            "ends": campaign.end_time,
            "goal": campaign.goal_goal_kpi.goal_name,
            "goal_kpi": campaign.goal_kpi,
            "context_list": campaign.context_list,
            "startDate": campaign.start_time
        }
        data.append(dict)

    try:
        sorted_data = sorted(data, key=lambda x: x['created_on'], reverse=True)
    except ValueError as e:
        print("Error: Date format mismatch or invalid date encountered in the 'created_on' field.")
        return None

    response = {
        'data': sorted_data,
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
    }
    return response







@campaign_blueprint.route('/getcampaigndetails', methods=['POST'])
@login_required
def getCampaignDetails():
    request_data = request.json
    req_order_id = request_data["order_id"]

    campaign_obj_list = Campaign.query.filter_by(order_id = req_order_id ).all()
    data =[]

    for campaign_obj in campaign_obj_list :
        # print(campaign_obj.id, campaign_obj.campaign_type, campaign_obj.campaign_name)
        dict={}
        dict["order_id"]=campaign_obj.order_id
        dict["campaignName"]=campaign_obj.campaign_name
        # dict["created_by"] = campaign_obj.user_details.name
        dict["totalBudget"] = campaign_obj.total_budget 
        dict["maxChangeInBudget"] = campaign_obj.max_change_in_budget 
        # dict["created_on"] = campaign_obj.created_on
        # dict["last_modified_on"] = campaign_obj.modified_on
        dict["brand"] = campaign_obj.brand.brand_name
        dict["region"] = campaign_obj.region.region_name
        dict["campaign_status"] = campaign_obj.campaign_status
        dict["endDate"]= campaign_obj.end_time
        dict["startDate"]= campaign_obj.start_time
        dict["goal"] = campaign_obj.goal_goal_kpi.goal_name
        dict["goalKPI"] = campaign_obj.goal_kpi
        dict["contexts"] = campaign_obj.context_list
        dict["audienceIds"] = campaign_obj.audience_ids
        dict["orderPONumber"] = campaign_obj.orderPO_number
        dict["domainNames"] = campaign_obj.domain_names
        dict["suggestion"] = campaign_obj.suggestions
        dict["product_tracking_list"] = campaign_obj.product_tracking_list

        
        
        # print(dict)
        data.append(dict)
        # print(data)
        # data= {}
    response = {}
    response['data'] = data
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    #logger.debug(response)
    return response    