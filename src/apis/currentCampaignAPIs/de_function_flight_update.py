from flask import Blueprint, jsonify,session,request,Response
import logging
from flask_login import login_required 
from models import Campaign,LineItems
from sqlalchemy.sql import extract
import requests
from apis.createCampaignAPIs.placeorderamazonAPI import get_access_token
from settings.config import advertiser_id,refresh_token,client_id,profile_id
import pandas as pd
from datetime import timedelta,datetime
import json
from database import db
from apis.currentCampaignAPIs.approveordenyreco import getlineItemDetailsfromDSP


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

editcampaign_blueprint = Blueprint('editcampaign', __name__)

editcampaign_store = {}

flight_period= 13


def add_flights(put_request_payload, end_date, flight_period):

    flights = put_request_payload['budget']['flights']

    # updates in n days flight
    flights[len(flights)-2]['endDateTime'] = (end_date).strftime('%Y-%m-%d %X') + " UTC"
    days = int((end_date - pd.to_datetime(flights[len(flights)-2]['startDateTime']).tz_convert(None)).days)
    flights[len(flights)-2]['amount'] = round(((flights[len(flights)-3]['amount']) / flight_period) * days)

    # update in 1$ flight
    flights[len(flights)-1]['startDateTime'] = pd.to_datetime(end_date + timedelta(0, 1)).strftime('%Y-%m-%d %X') + " UTC"
    flights[len(flights)-1]['endDateTime'] = pd.to_datetime(end_date + timedelta(flight_period)).strftime('%Y-%m-%d %X') + " UTC"

    return flights
    

def getcampaigndetailsfromDSP(orderID):
    print("Retrieving camapign Details (GET call)")
    try:
        url = f"https://advertising-api.amazon.com/dsp/orders/{orderID}"

        headers = {
            'Amazon-Advertising-API-ClientId': client_id,
            'Amazon-Advertising-API-Scope': profile_id,
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {get_access_token(refresh_token)}',
            'Accept': 'application/vnd.dsporders.v2.3+json',
        }

        response = requests.request("GET", url, headers=headers)

        print("EDIT CAMPAIGN GET CALL RESPONSE :", response)
        return response.json()
    
    except Exception as e:
        print(f"Error occured while getting order details with id: {orderID} with error : {str(e)}")
        return ((f"Error occured while getting order details with id: {orderID} with error : {str(e)}"))


def updatecamapigncall(put_request_payload, updated_end_date):
    print("Updating camapign Details (POST call)")
    url = "https://advertising-api.amazon.com/dsp/orders/"

    new_flights = add_flights(put_request_payload, updated_end_date)

    put_request_payload['budget']['flights'] = new_flights

    payload = [put_request_payload]
    # print("Campaign PUT call Paylaod :", payload)
    data =json.dumps(payload)
    headers = {
        'Amazon-Advertising-API-ClientId': client_id,
        'Amazon-Advertising-API-Scope': profile_id,
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token(refresh_token)}',
        'Accept': 'application/vnd.dsporders.v2.3+json',
    }
   
    put_response = requests.request("PUT", url, headers=headers, data=data)
    json_put_response = put_response.json()

    if 'orderId' in json_put_response[0]:
        orderId = json_put_response[0]['orderId']
        print(f"Date Updated for order with ID : {orderId}")
        camp_obj = Campaign.query.filter_by(order_id = orderId).first()
        camp_obj.order_budget["flights"] = new_flights
        camp_obj.end_time = updated_end_date
        db.session.commit()
        print("New Fligths for order Updated in db")
   

    print("Update flight PUT Call Response", put_response)

    return put_response.json()




@editcampaign_blueprint.route('/editcampaign', methods=['POST'])
# @login_required
def editCampaign():
    request_data = request.json
    orderId = request_data['order_id']
    updated_end_date = request_data['endDate']

    updated_end_date = pd.to_datetime(updated_end_date)
    get_response = getcampaigndetailsfromDSP(orderId)
    # print( "Campaign_getCall_response : ", get_response)

    put_request_payload = get_response

    put_response = updatecamapigncall(put_request_payload,updated_end_date)


    response = {}
    response['data'] = {"order_update_response" : put_response }
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    return response










