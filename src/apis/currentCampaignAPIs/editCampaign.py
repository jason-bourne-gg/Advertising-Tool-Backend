'''from flask import Blueprint, jsonify,session,request,Response
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


def add_flights(put_request_payload, end_date):
    try:
        flights = put_request_payload['budget']['flights']

        # updates in n days flight
        flights[len(flights)-2]['endDateTime'] = (end_date).strftime('%Y-%m-%d %X') + " UTC"
        days = int((end_date - pd.to_datetime(flights[len(flights)-2]['startDateTime']).tz_convert(None)).days)
        flights[len(flights)-2]['amount'] = round(((flights[len(flights)-3]['amount']) / flight_period) * days)
        if(flights[len(flights)-2]['amount'] < 1):
            flights[len(flights)-2]['amount'] = 1

        # update in 1$ flight
        flights[len(flights)-1]['startDateTime'] = pd.to_datetime(end_date + timedelta(0, 1)).strftime('%Y-%m-%d %X') + " UTC"
        flights[len(flights)-1]['endDateTime'] = pd.to_datetime(end_date + timedelta(flight_period)).strftime('%Y-%m-%d %X') + " UTC"
        flights[len(flights)-1]['amount'] = 1
        
        # print(flights)
        return flights

    except KeyError as e:
        # Handle missing keys in the 'put_request_payload' dictionary
        raise ValueError(f"Invalid 'put_request_payload': Missing key: {e}")
    
    except IndexError as e:
        # Handle index errors (e.g., if 'flights' list is empty or doesn't have enough elements)
        raise ValueError(f"Invalid 'flights' list in 'put_request_payload': {e}")

    except Exception as e:
        # Handle any other unexpected errors
        raise ValueError(f"An error occurred while adding flights: {e}")
    

def getcampaigndetailsfromDSP(orderID):
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

        print("get campaign details", response)
        return response.json()
    
    except Exception as e:
        print(f"Error occured while getting order details with id: {orderID} with error : {str(e)}")
        return ((f"Error occured while getting order details with id: {orderID} with error : {str(e)}"))


def updatecamapigncall(put_request_payload, updated_end_date):
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
        camp_obj.modified_on = datetime.utcnow()
        db.session.commit()
        print("New Fligths for order Updated in db")
   

    print("Update flight PUT Call Response", put_response)

    return put_response.json()


def getalllineitemsforOrderId (orderId):
    print("Retrieving lineItem Details (GET call)")
    url = "https://advertising-api.amazon.com/dsp/lineItems/"

    headers = {
        'Amazon-Advertising-API-ClientId': client_id,
        'Amazon-Advertising-API-Scope': profile_id,
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token(refresh_token)}',
        'Accept': 'application/vnd.dsplineitems.v2.2+json', 
        }

    params = {
        "advertiserIdFilter" : advertiser_id, 
        "orderIdFilter": f'{orderId}'
    }

    response = requests.request("GET", url, headers=headers, params = params)

    # print(response.json())
    return (response.json())


def updateLineItemDate (getCallResponse, updated_end_date):

    url = "https://advertising-api.amazon.com/dsp/lineItems/"

    # payload = [{'endDateTime' : updated_end_date, **getCallResponse} ] ....don't knw why this isn't working
    getCallResponse['endDateTime'] = updated_end_date
    new_payload = [getCallResponse]
    data =json.dumps(new_payload)
    headers = {
        'Amazon-Advertising-API-ClientId': client_id,
        'Amazon-Advertising-API-Scope': profile_id,
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token(refresh_token)}',
        'Accept': 'application/vnd.dsplineitems.v3.2+json',   
    }

    response = requests.request("PUT", url, headers=headers, data=data)
    # print(response.json())
    return (response.json())

@editcampaign_blueprint.route('/editcampaign', methods=['POST'])
@login_required
def editCampaign():
    request_data = request.json
    orderId = request_data["order_id"]
    updated_end_date = request_data["endDate"]
    print(orderId,updated_end_date)

    updated_end_date = pd.to_datetime(updated_end_date)
    get_response = getcampaigndetailsfromDSP(orderId)
    # print( "Campaign_getCall_response : ", get_response)

    put_request_payload = get_response

    put_response = updatecamapigncall(put_request_payload,updated_end_date)
    
    updated_lineItem_array = [] 
    if 'orderId' in put_response[0]:
        print(f"Date Updated for order with ID : {orderId}")

        lineItemsData = getalllineitemsforOrderId(orderId)
        # print(lineItemsData)

        line_item_ids = [item['lineItemId'] for item in lineItemsData['response']]
        print("line_item_ids array : ", line_item_ids)

        updated_end_date = pd.to_datetime(updated_end_date+timedelta(flight_period)).strftime('%Y-%m-%d %X')+" UTC"
        for line_item_id in line_item_ids:
            date_string_without_utc = updated_end_date.replace(' UTC', '')
            datetime_object = datetime.strptime(date_string_without_utc, '%Y-%m-%d %H:%M:%S')
            
            getCallResponse = getlineItemDetailsfromDSP(line_item_id)
            print(f"updating lineItem Date for Adgroup with id : {line_item_id}")
            putcallresponse = updateLineItemDate(getCallResponse, updated_end_date)

            if 'lineItemId' in putcallresponse[0]:

                print(f"updated lineItem EndDate for Adgroup with id : {line_item_id} with response: {putcallresponse}")
                lineItemId = putcallresponse[0]['lineItemId']
                lineitem_obj = LineItems.query.filter_by(line_item_id = lineItemId).first()
                lineitem_obj.end_time = datetime_object
                db.session.commit()
                print(f"New Date for lineitem {lineItemId} Updated in db")
            
            else:
                print(f"Error in updating EndDate for lineitem with id {line_item_id}")   
                return Response(f"Error in updating Enddate for lineitem with id {line_item_id}", 500) 

            updated_lineItem_array.append(putcallresponse)



    else:
        print("Error in Updating flight for order")
        return put_response

    response = {}
    response['data'] = {"updated_lineItem_array" : updated_lineItem_array, "order_update_response" : put_response }
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    return response

'''











# error handled code

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
import calendar


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

editcampaign_blueprint = Blueprint('editcampaign', __name__)

editcampaign_store = {}

# flight_period= 13


def add_flights(put_request_payload, end_date):
    try:
        updated_date = pd.to_datetime(end_date)
        flights = put_request_payload['budget']['flights']
        min_threh=7
        number_of_days_increased = int((updated_date - (pd.to_datetime(flights[-2]['endDateTime']).tz_convert(None))).days)+1


        #regular update (4th last flight is going on or flight before it)
        if pd.to_datetime(flights[len(flights)-4]['endDateTime']).tz_convert(None)>pd.to_datetime('today'):
            #just update order end date and than 1 dollar flight accordingly
            print(1)
            flights[len(flights)-2]['endDateTime']= pd.to_datetime(updated_date).strftime('%Y-%m-%d %X')+" UTC"
            flights[len(flights)-1]['startDateTime']=pd.to_datetime(updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
            flights[len(flights)-1]['endDateTime']=pd.to_datetime(updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"

            
        #3rd last flight is running 
        elif pd.to_datetime(flights[len(flights)-3]['endDateTime']).tz_convert(None)>pd.to_datetime('today'):
            print(2)
            ##calculating budget per day
            n_days = int(((pd.to_datetime(flights[-3]['endDateTime']).tz_convert(None)) - (pd.to_datetime(flights[-3]['startDateTime']).tz_convert(None)-timedelta(0,1))).days+1)
            flight_budget_day = flights[len(flights)-3]['amount']/n_days
            
            ##we proceed to create new flight only if we have some considerable change
            if( number_of_days_increased > min_threh):
                #(create one regular flight and  update n days flight and 1 dollar flight )
                #n days->regular upcoming flight
                flight_start=pd.to_datetime(flights[len(flights)-2]['startDateTime']).tz_convert(None)
                
                #end date of flight according to new monthy logic
                num_days_in_month=calendar.monthrange(flight_start.year, flight_start.month)[1]
                if(flight_start.day>15):
                    flight_period= num_days_in_month-flight_start.day+1
                    if flight_period<min_threh:
                        flight_period=flight_period+15
                else:
                    flight_period= 15-flight_start.day+1
                    if flight_period<min_threh:
                        flight_period=flight_period+(num_days_in_month-15)
                #updated_date->order_end_date_updated by user
                if updated_date <= (flight_start+timedelta(flight_period)-timedelta(0,1)):
                    flight_end = updated_date
                else:
                    flight_end = (flight_start+timedelta(flight_period)-timedelta(0,1))
                
                flights[len(flights)-2]['endDateTime']= flight_end.strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-2]['amount']=round(flight_budget_day*int((flight_end-flight_start).days+1))
                
                #1 dollar to n days
                if updated_date > flight_end:
                    flights[len(flights)-1]['startDateTime'] = (flight_end+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                    flights[len(flights)-1]['endDateTime'] = (updated_date).strftime('%Y-%m-%d %X')+" UTC"
                    flights[len(flights)-1]['amount'] = round(flight_budget_day*int((updated_date-flight_end).days+1))
                    
                    new_flight = {}
                    new_flight['startDateTime'] = (updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                    new_flight['endDateTime'] = (updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"
                    new_flight['amount'] = 1
                    
                    flights.append(new_flight)
                    
                else:
                    flights[len(flights)-1]['startDateTime'] = (updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                    flights[len(flights)-1]['endDateTime'] = (updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"
                    flights[len(flights)-1]['amount'] = 1
                            
                
            else:
                #update end date and 1 dollar flight
                flights[len(flights)-2]['endDateTime']= pd.to_datetime(updated_date).strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-1]['startDateTime']=pd.to_datetime(updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-1]['endDateTime']=pd.to_datetime(updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"


        #second last flight is running (n days flight)
        elif pd.to_datetime(flights[len(flights)-2]['endDateTime']).tz_convert(None)>pd.to_datetime('today'):
            print(3)
            n_days = int(((pd.to_datetime(flights[-2]['endDateTime']).tz_convert(None)) - (pd.to_datetime(flights[-2]['startDateTime']).tz_convert(None)-timedelta(0,1))).days+1)
            flight_budget_day = flights[len(flights)-2]['amount']/n_days
            
            if number_of_days_increased< min_threh:
                #update end date and 1 dollar flight
                flights[len(flights)-2]['endDateTime']= pd.to_datetime(updated_date).strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-1]['startDateTime']=pd.to_datetime(updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-1]['endDateTime']=pd.to_datetime(updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"
            else:
                #1dollar->upcming  
                flight_start=pd.to_datetime(flights[len(flights)-1]['startDateTime']).tz_convert(None)
                num_days_in_month=calendar.monthrange(flight_start.year, flight_start.month)[1]
                if(flight_start.day>15):
                    flight_period= num_days_in_month-flight_start.day+1
                    if flight_period<min_threh:
                        flight_period=flight_period+15
                else:
                    flight_period= 15-flight_start.day+1
                    if flight_period<min_threh:
                        flight_period=flight_period+(num_days_in_month-15)

                if updated_date <= (flight_start+timedelta(flight_period)-timedelta(0,1)):
                    flight_end = updated_date
                else:
                    flight_end = (flight_start+timedelta(flight_period)-timedelta(0,1))
                
                flights[len(flights)-1]['endDateTime']= flight_end.strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-1]['amount']=round(flight_budget_day*int((flight_end-flight_start).days+1))
            
                #new -> ndays and 1 dollar

                if updated_date > flight_end:
                                
                    new_flight = {}
                    new_flight['startDateTime'] = (flight_end+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                    new_flight['endDateTime'] = (updated_date).strftime('%Y-%m-%d %X')+" UTC"
                    new_flight['amount'] = round(flight_budget_day*int((updated_date-flight_end).days+1))
                    flights.append(new_flight)
                    
                    new_flight = {}
                    new_flight['startDateTime'] = (updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                    new_flight['endDateTime'] = (updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"
                    new_flight['amount'] = 1
                    flights.append(new_flight)
                    
                else:
                    flights[len(flights)-1]['startDateTime'] = (updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                    flights[len(flights)-1]['endDateTime'] = (updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"
                    flights[len(flights)-1]['amount'] = 1
            
        ##last flight is running (1$ flight)
        else:
            print(4)
            n_days = int(((pd.to_datetime(flights[-2]['endDateTime']).tz_convert(None)) - (pd.to_datetime(flights[-2]['startDateTime']).tz_convert(None)-timedelta(0,1))).days+1)
            flight_budget_day = flights[len(flights)-2]['amount']/n_days
            
            if number_of_days_increased< min_threh:
                #update end date & budget of 1 dollar flight 
                flight_start=pd.to_datetime(flights[len(flights)-1]['startDateTime']).tz_convert(None)
                flights[len(flights)-1]['endDateTime']=pd.to_datetime(updated_date).strftime('%Y-%m-%d %X')+" UTC"
                flights[len(flights)-1]['amount'] = round(flight_budget_day*int((updated_date-flight_start).days+1))
                
            else:
                flight_start=pd.to_datetime(flights[len(flights)-1]['startDateTime']).tz_convert(None)
                flights[len(flights)-1]['amount'] = round(flight_budget_day*int((updated_date-flight_start).days+1))
                
                count =0
                flight_end = pd.to_datetime(flights[len(flights)-1]['endDateTime']).tz_convert(None)

                while flight_end < updated_date:
                    print(flight_end)
                    if count==1:
                        new_flight = {}
                        new_flight['startDateTime'] = (flight_end+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                        new_flight['endDateTime'] = (updated_date).strftime('%Y-%m-%d %X')+" UTC"
                        new_flight['amount'] = round(flight_budget_day*int((updated_date-flight_end).days+1))
                        flights.append(new_flight)
                        
                        flight_end=updated_date
                        
                    else:
                        count = count+1
                        new_flight = {}
                        new_flight['startDateTime'] = (flight_end+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                        flight_start = flight_end
                        num_days_in_month=calendar.monthrange(flight_end.year, flight_end.month)[1]
                        
                        if(flight_end.day>15):
                            flight_period= num_days_in_month-flight_end.day+1
                            if flight_period<min_threh:
                                flight_period=flight_period+15
                        else:
                            flight_period= 15-flight_end.day+1
                            if flight_period<min_threh:
                                flight_period=flight_period+(num_days_in_month-15)

                        if updated_date <= (flight_end+timedelta(flight_period)):
                            flight_end = updated_date
                        else:
                            flight_end = (flight_end+timedelta(flight_period))

                        new_flight['endDateTime'] = (flight_end).strftime('%Y-%m-%d %X')+" UTC"
                        new_flight['amount'] = round(flight_budget_day*int((flight_end-flight_start).days+1))

                        flights.append(new_flight)
                    
                new_flight = {}
                new_flight['startDateTime'] = (updated_date+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['endDateTime'] = (updated_date+timedelta(15)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['amount'] = 1
                
                flights.append(new_flight)
                

        return flights

    except KeyError as e:
        # Handle missing keys in the 'put_request_payload' dictionary
        raise ValueError(f"Invalid 'put_request_payload': Missing key: {e}")
    
    except IndexError as e:
        # Handle index errors (e.g., if 'flights' list is empty or doesn't have enough elements)
        raise ValueError(f"Invalid 'flights' list in 'put_request_payload': {e}")

    except Exception as e:
        # Handle any other unexpected errors
        raise ValueError(f"An error occurred while adding flights: {e}")
    

def getcampaigndetailsfromDSP(orderID):
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

        print("get campaign details", response)
        return response.json()
    
    except Exception as e:
        print(f"Error occured while getting order details with id: {orderID} with error : {str(e)}")
        return ((f"Error occured while getting order details with id: {orderID} with error : {str(e)}"))


def updatecamapigncall(put_request_payload, updated_end_date):
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
        camp_obj.modified_on = datetime.utcnow()
        db.session.commit()
        print("New Fligths for order Updated in db")
   

    print("Update flight PUT Call Response", json_put_response)

    return put_response.json()


def getalllineitemsforOrderId (orderId):
    print("Retrieving lineItem Details (GET call)")
    url = "https://advertising-api.amazon.com/dsp/lineItems/"

    headers = {
        'Amazon-Advertising-API-ClientId': client_id,
        'Amazon-Advertising-API-Scope': profile_id,
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token(refresh_token)}',
        'Accept': 'application/vnd.dsplineitems.v2.2+json', 
        }

    params = {
        "advertiserIdFilter" : advertiser_id, 
        "orderIdFilter": f'{orderId}'
    }

    response = requests.request("GET", url, headers=headers, params = params)

    # print(response.json())
    return (response.json())


def updateLineItemDate (getCallResponse, updated_end_date):

    url = "https://advertising-api.amazon.com/dsp/lineItems/"

    # payload = [{'endDateTime' : updated_end_date, **getCallResponse} ] ....don't knw why this isn't working
    getCallResponse['endDateTime'] = updated_end_date
    new_payload = [getCallResponse]
    data =json.dumps(new_payload)
    headers = {
        'Amazon-Advertising-API-ClientId': client_id,
        'Amazon-Advertising-API-Scope': profile_id,
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {get_access_token(refresh_token)}',
        'Accept': 'application/vnd.dsplineitems.v3.2+json',   
    }

    response = requests.request("PUT", url, headers=headers, data=data)
    # print(response.json())
    return (response.json())


def update_line_item_end_date(line_item_id, updated_end_date):
    try:
        date_string_without_utc = updated_end_date.replace(' UTC', '')
        datetime_object = datetime.strptime(date_string_without_utc, '%Y-%m-%d %H:%M:%S')
        
        get_call_response = getlineItemDetailsfromDSP(line_item_id)
        print(f"Updating lineItem Date for Adgroup with id: {line_item_id}")
        put_call_response = updateLineItemDate(get_call_response, updated_end_date)

        if 'lineItemId' in put_call_response[0]:
            line_item_id_from_response = put_call_response[0]['lineItemId']
            line_item_obj = LineItems.query.filter_by(line_item_id=line_item_id_from_response).first()
            
            if line_item_obj:
                line_item_obj.end_time = datetime_object
                db.session.commit()
                print(f"New Date for lineitem {line_item_id_from_response} Updated in db")
            else:
                print(f"LineItem with id {line_item_id_from_response} not found in the database")
        else:
            print(f"Error in updating EndDate for lineitem with id {line_item_id}")
            return False
        
        return True
    except Exception as e:
        print(f"An error occurred while updating lineItem EndDate: {str(e)}")
        return False


@editcampaign_blueprint.route('/editcampaign', methods=['POST'])
@login_required
def edit_campaign():
    try:
        request_data = request.json
        order_id = request_data["order_id"]
        updated_end_date = request_data["endDate"]
        # print(order_id, updated_end_date)
        updated_end_date = pd.to_datetime(updated_end_date)

        get_response = getcampaigndetailsfromDSP(order_id)
        put_request_payload = get_response
        put_response = updatecamapigncall(put_request_payload, updated_end_date)
        
        updated_line_item_array = []
        
        if 'orderId' in put_response[0]:
            print(f"Date Updated for order with ID: {order_id}")

            line_items_data = getalllineitemsforOrderId(order_id)
            line_item_ids = [item['lineItemId'] for item in line_items_data['response']]
            print("line_item_ids array: ", line_item_ids)

            flight_period = timedelta(days=15)  # Assuming you have the flight period defined
            
            updated_end_date_with_period = pd.to_datetime(updated_end_date + flight_period).strftime('%Y-%m-%d %X') + " UTC"
            
            for line_item_id in line_item_ids:
                success = update_line_item_end_date(line_item_id, updated_end_date_with_period)
                
                if success:
                    print(f"Successfully updated lineItem EndDate for Adgroup with id: {line_item_id}")
                    updated_line_item_array.append(f"Successfully updated lineItem EndDate for Adgroup with id: {line_item_id}")
                else:
                    print(f"Error in updating EndDate for lineitem with id {line_item_id}")
                    updated_line_item_array.append(f"Failed to update lineItem EndDate for Adgroup with id: {line_item_id}")
                    # return Response(f"Error in updating Enddate for lineitem with id {line_item_id}", 500)

        else:
            print("Error in Updating flight for order")
            return put_response
        
        response = {
            'data': {"updated_lineItem_array": updated_line_item_array, "order_update_response": put_response},
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
        
        return response
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return Response("An error occurred while processing the request", 500)
