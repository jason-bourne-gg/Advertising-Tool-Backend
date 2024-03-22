from flask import Blueprint, jsonify,session,request
import datetime
import logging
from flask_login import login_required 
import requests
import json
from models import Suggestion
from database import db
from sqlalchemy import desc, func


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

budget_blueprint = Blueprint('budget', __name__)

brand_store = {}

@budget_blueprint.route('/getbudget', methods=['GET', 'POST'])
@login_required
def getBudget():
   
    start_date = request.json["start_date"]
    end_date = request.json["end_date"]
    start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()

    context_array = request.json["contexts"]
    # print(context_array)
    # query = select context, weekly_budget, no_of_line_items from recommended_settings (Suggestion) table where brand_id =  request_json["brand"]["id"] and context _in[context_array] ;

    subquery = db.session.query(func.max(Suggestion.last_updated_on)).filter(
        Suggestion.line_item_count > 0,
        Suggestion.brand_id == request.json["brand"]["id"]
        ).scalar_subquery()

    row_objs = Suggestion.query.filter(
        Suggestion.brand_id == request.json["brand"]["id"],
        Suggestion.context.in_(context_array),
        Suggestion.last_updated_on == subquery,
        Suggestion.line_item_count > 0
    ).all()
    print(row_objs)

    # formula = sum(all weekly_budget for selected contexts * no of line items) * (no of weeks +1)
    weeks = int((end_date - start_date).days / 7)
    print("weeks", weeks)
    calc_budget =  sum(row_obj.weekly_budget * row_obj.line_item_count for row_obj in row_objs) * (weeks+1)
    print("Budget", calc_budget)


    response = {}
    response['data'] = [{"total_budget" : calc_budget, "currency" : "$"}]
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    logger.debug(response)
    return response   
 
    