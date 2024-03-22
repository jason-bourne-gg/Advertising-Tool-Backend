from flask import Blueprint, jsonify,session,request,Response
import logging
from flask_login import login_required 
from models import CampaignRecommendations,LineItems,Brand
from sqlalchemy.sql import extract
import requests
from apis.createCampaignAPIs.placeorderamazonAPI import get_access_token
from settings.config import advertiser_id,refresh_token,client_id,profile_id
import pandas as pd
from datetime import timedelta,datetime
import json
from database import db
from sqlalchemy import and_,text
from datetime import time
from settings.config import (
    storage_account_name,
    account_access_key,
    sas_token,
    container_name,
    connection_string,
    advertiser_id,
)
from azure.storage.blob import BlobServiceClient
import io
from apis.createCampaignAPIs.placeorderamazonAPI import readCreativesintoDF,activateLineitems


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

approvedenyreco_blueprint = Blueprint('approvedenyreco', __name__)

approvedenyreco_store = {}

date_format = '%Y-%m-%d %H:%M:%S %Z'


def updateCreativesRecoLineItem(ContextlineItemIdMappingArray, brand_id):
    try:
        brand_obj = Brand.query.filter_by(id = brand_id).first()
        brand_name = brand_obj.brand_name
        file_df = readCreativesintoDF(brand_name)
        print(file_df)

        mapping_df = pd.DataFrame(ContextlineItemIdMappingArray, columns=['lineItemId', 'lineType', 'deviceType'])
        print("mapping_df :", mapping_df )

        # Create a dictionary to store lineitem IDs and their respective creatives
        lineitem_creatives_mapping = {}

        # Iterate through the file_df and mapping_df
        for index, row in file_df.iterrows():
            line_type = row['lineType']
            device_type = row['deviceType']
            creatives = row['Creatives'].split(', ')

            # Find corresponding lineitem IDs from the mapping_df
            matching_lineitems = mapping_df[(mapping_df['lineType'] == line_type) & (mapping_df['deviceType'] == device_type)]

            # Append the list of creatives to the lineitem IDs
            for lineitem_id in matching_lineitems['lineItemId']:
                if lineitem_id not in lineitem_creatives_mapping:
                    lineitem_creatives_mapping[lineitem_id] = []
                lineitem_creatives_mapping[lineitem_id].extend(creatives)

        # Print the mapping
        print("lineitem_creatives_mapping : " ,lineitem_creatives_mapping )

        creatives_updation_array = []

        for line_item_id, creative_ids in lineitem_creatives_mapping.items():
            try:
                for creative_id in creative_ids:
                    url = "https://advertising-api.amazon.com/dsp/lineItemCreativeAssociations"
                    creative_payload = {
                        "advertiserId": str(advertiser_id),
                        "operation": "CREATE",
                        "associations": [
                            {"lineItemId": line_item_id, "creativeId": creative_id}
                        ],
                    }
                    creatives_payload_str = json.dumps(creative_payload)
                    headers = {
                        "Amazon-Advertising-API-ClientId": client_id,
                        "Amazon-Advertising-API-Scope": profile_id,
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {get_access_token(refresh_token)}",
                        "Accept": "application/vnd.dsplineitemcreativeassociations.v2.1+json",
                    }

                    response = requests.request("POST", url, headers=headers, data=creatives_payload_str)
                    response_json = response.json()
                    print(response_json)

                    while('message' in response_json and response_json['message'] == 'Too Many Requests'):
                        print("Retrying for 'Too many request error' ERROR after 5 sec")
                        time.sleep(5)
                        response = requests.request("POST", url, headers=headers, data=creatives_payload_str)
                        response_json = response.json()
                        print("Retry response = ",response_json)

                    if "success" in response_json[0]:
                        creatives_updation_array.append(f"{line_item_id} : SUCCESS")

                    else:
                        creatives_updation_array.append(f"{line_item_id} : FAILED")

                    print(creatives_updation_array)

            except Exception as e:
                print("error:" + str(e) )

        return creatives_updation_array

    except Exception as e:
        logger.error(str(e))
        return []


def updateDefaultDomains(lineItemIdArray):
    try:
        domain_updation_array = []

        for line_item_id in lineItemIdArray:
            url = "https://advertising-api.amazon.com/dsp/targeting/domain"

            file_name = "default_domain_list.csv"
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(container_name)

            blob_name = f"DomainLists/DEFAULT/{file_name}"

            blob_client = container_client.get_blob_client(blob_name)
            blob_data = blob_client.download_blob().readall()

            file_stream = io.BytesIO(blob_data)
            df = pd.read_csv(file_stream)
            domain_names = df.head(99).to_csv(index=False, header=False).strip().split("\n")

            domain_payload = [
                {
                    "lineItemId": line_item_id,
                    "inheritFromAdvertiser": True,
                    "targetingType": "INCLUDE",
                    "domainNames": domain_names,
                }
            ]

            domain_payload_str = json.dumps(domain_payload)
            headers = {
                "Amazon-Advertising-API-ClientId": client_id,
                "Amazon-Advertising-API-Scope": profile_id,
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_access_token(refresh_token)}",
                "Accept": "application/vnd.dspupdatedomaintargeting.v1+json",
            }

            try: 
                response = requests.request("PUT", url, headers=headers, data=domain_payload_str )
                response_json = response.json()
                print(response_json)

                # Retry Logic in case of TOO MANY REQ error 
                while('message' in response_json and response_json['message'] == 'Too Many Requests'):
                    print("Retrying for 'Too many request error' ERROR after 5 sec")
                    time.sleep(5)
                    response = requests.request("PUT", url, headers=headers, data=domain_payload_str )
                    response_json = response.json()
                    print("Retry response = ",response_json)

                if "lineItemId" in response_json[0]:
                    domain_updation_array.append(f"{line_item_id} : SUCCESS")

            except Exception as e:
                print(f"Could not update domains for lineitem with id : {line_item_id} because of Error : " + str(e))
                domain_updation_array.append(f"{line_item_id} : FAILED")

        return domain_updation_array

    except Exception as e:
        logger.error(str(e))
        return []


def update_payload(payload, reco_mapping):
    for key, value in reco_mapping.items():
        keys = key.split('.')
        current_dict = payload
        for k in keys[:-1]:
            current_dict = current_dict[k]
        current_dict[keys[-1]] = value
    return payload


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


def createlineitem (create_call_paylaod, orderId ):
    line_item_id_array = []
    SD_line_item_ID_array = []
    creatives_line_mapping_array = []
    try: 
        for line_item in create_call_paylaod:
            url = "https://advertising-api.amazon.com/dsp/lineItems/"

            payload = [{"orderId": f"{orderId}", **line_item}]

            payload_str = json.dumps(payload)
            headers = {
                "Amazon-Advertising-API-ClientId": client_id,
                "Amazon-Advertising-API-Scope": profile_id,
                "Content-Type": "application/json",
                "Authorization": f"Bearer {get_access_token(refresh_token)}",
                "Accept": "application/vnd.dsplineitems.v3.2+json",
            }

            response = requests.request("POST", url, headers=headers, data=payload_str)
            response_json = response.json()
            print("LineItemPostCallResponse: ", response_json)

            if "lineItemId" in response_json[0]:
                lineItemId = response_json[0]["lineItemId"]
                print(f"Putting line item data in the database for lineitemId = {lineItemId}")
                try:
                    line_item_db = LineItems(
                        order_id=orderId,
                        line_item_id=lineItemId,
                        line_item_name=line_item["name"],
                        line_item_type=line_item["lineItemType"],
                        start_time=datetime.strptime(line_item["startDateTime"], date_format),
                        end_time=datetime.strptime(line_item["endDateTime"], date_format),
                        line_item_classification=line_item["lineItemClassification"],
                        frequency_cap=line_item["frequencyCap"],
                        targeting=line_item["targeting"],
                        bidding=line_item["bidding"],
                        budget=line_item["budget"],
                        optimization=line_item["optimization"],
                        creatives=line_item["creativeOptions"],
                    )
                    db.session.add(line_item_db)
                    db.session.commit()
                    print(f"Data inserted successfully for line_item_id: {lineItemId}")
                    line_item_id_array.append(lineItemId)
                    # print(line_item_id_array)
                    print(line_item['lineItemType'])
                    if line_item['lineItemType'] == 'STANDARD_DISPLAY':
                        SD_line_item_ID_array.append(lineItemId)
                    
                    elements = line_item["name"].split('|')
                    lineType = elements[1].strip()
                    deviceType = elements[2].strip()
                    creatives_line_mapping_array.append ([lineItemId, lineType, deviceType])
                
                except Exception as e:
                    print(f"Data could not be inserted successfully for line_item_id: {lineItemId}. Error :" + str(e)) 
                    line_item_id_array.append(lineItemId)
                    if line_item['lineItemType'] == 'STANDARD_DISPLAY':
                        SD_line_item_ID_array.append(lineItemId)
                
            else:
                print(f"Request failed with status code: {response.status_code} .")
                # return jsonify({f"Request failed with status code: {response.status_code}"})

        return (line_item_id_array, SD_line_item_ID_array,creatives_line_mapping_array )

    except Exception as e:
        logger.error(str(e))
        print("error in creating line item:", str(e))
        error_message = f"Recommended Line item could not be created. Error: {str(e)}"
        response = jsonify({"error": error_message})
        response.status_code = 500  # Internal Server Error
        return response


def deactivateLineitems(lineItemId, status):
    try:
        url = f"https://advertising-api.amazon.com/dsp/lineItems/{lineItemId}/deliveryActivationStatus"

        headers = {
            "Amazon-Advertising-API-ClientId": client_id,
            "Amazon-Advertising-API-Scope": profile_id,
            # "Content-Type": "application/json",
            "Authorization": f"Bearer {get_access_token(refresh_token)}",
            "Accept": "application/vnd.dsplineitemsdeliveryactivationstatus.v3+json",
        }

        # params = {"status": "ACTIVE"}
        # params = {"status": "INACTIVE"}
        params = {"status": f"{status}"}

        response = requests.request("POST", url, headers=headers, params=params)

        if response.status_code != 204:
            error_message = f"Error in activatinglineItem {lineItemId}: {response.json()}"
            print("error:" +  error_message, response.json())
            raise Exception(error_message)

        else:
            print (f"LineItem with {lineItemId} DEACTIVATED SUCCESSFULLY")
            return Response (f"LineItem with {lineItemId} DEACTIVATED SUCCESSFULLY")    

    except Exception as e:
        logger.error(str(e))
        error_message = {"LineItem deactivation status": "FAILED", "error": str(e)}
        print(error_message)
        raise Exception(error_message)

    
def getlineItemDetailsfromDSP(lineItemId):
    try:
        url = f"https://advertising-api.amazon.com/dsp/lineItems/{lineItemId}"

        headers = {
            'Amazon-Advertising-API-ClientId': client_id,
            'Amazon-Advertising-API-Scope': profile_id,
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {get_access_token(refresh_token)}',
            'Accept': 'application/vnd.dsplineitems.v3.2+json',
        }

        response = requests.request("GET", url, headers=headers)

        print("UPDATE LINEITEM GET CALL RESPONSE :", response)
        return response.json()
    
    except Exception as e:
        print(f"Error occured while getting lineitem details with id: {lineItemId}  with error : {str(e)}")
        return (f"Error occured while getting lineitem details with id: {lineItemId} with error : {str(e)}")


def updatecamapigncall(put_request_payload):
    try :
        url = "https://advertising-api.amazon.com/dsp/orders/"
        
        payload = [put_request_payload]

        data =json.dumps(payload)
        headers = {
            'Amazon-Advertising-API-ClientId': client_id,
            'Amazon-Advertising-API-Scope': profile_id,
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {get_access_token(refresh_token)}',
            'Accept': 'application/vnd.dsporders.v2.3+json',
        }
    
        put_response = requests.request("PUT", url, headers=headers, data=data)
        print("Reco Update Response",put_response.json()) 
        return put_response.json()

    
    except Exception as e:
        logger.error(str(e))
        print("error in updating flights:", str(e))
        error_message = f"Recommended flights could not be created. Error: {str(e)}"
        response = jsonify({"error": error_message})
        response.status_code = 500  # Internal Server Error
        return response


def updateLineItemData (getCallResponse):

    url = "https://advertising-api.amazon.com/dsp/lineItems/"

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


def updateDB(reco_id, user_action):
    try:
        lineItem_obj = CampaignRecommendations.query.filter(
            CampaignRecommendations.id == reco_id,
        ).first()

        if lineItem_obj:
            lineItem_obj.status = user_action
            lineItem_obj.date_of_user_action = datetime.utcnow()

            db.session.commit()
            print(f"Recommendation status for recommendation-ID {reco_id} changed to {user_action}")
        else:
            print(f"Line item with recommendation-ID {reco_id} not found in the database.")

    except Exception as e:
        print(f"Error occurred while updating the database: {e}")


@approvedenyreco_blueprint.route('/approvedenyreco', methods=['POST'])
@login_required
def editLineItem():
    try :
        request_data = request.json
        print(request_data)
        request_data = request_data['data']
        response = {}
                
        for item in request_data:
            lineItemId = item['lineItemId']
            user_action = item['user_action']
            order_id = item["orderId"]
            reco_id = item["id"]
            print(lineItemId,user_action)

            if user_action == "DENIED":
                updateDB(reco_id, user_action)
                response = {}
                response["status"] = {
                    "statusMessage": "Recommendation Denied As Per your request",
                    "statusCode" : 200
                }
                return response

            lineItem_obj = CampaignRecommendations.query.filter(
                CampaignRecommendations.id == reco_id,
            ).first()

            print("Operation to be performed on Recommendation", lineItem_obj.flag)

            if lineItem_obj.flag == None:
                return response("Could Not find operation to perform", 404)

            if lineItem_obj.flag == "UPDATE":
                try:
                    getCallResponse = getlineItemDetailsfromDSP (lineItemId)
                    if 'message' in getCallResponse:
                        print("Error in fetching details from Amazon")
                        return Response (f"Error in fetching details from Amazon", 500)  

                    reco_obj = lineItem_obj.recommendation_object
                    order_id = lineItem_obj.order_id
                    print("reco_obj =",reco_obj )
                    updated_payload = update_payload(getCallResponse, json.loads(reco_obj))
                    print(updated_payload)

                    put_req_paylaod = updateLineItemData(updated_payload)

                    if 'lineItemId' in put_req_paylaod[0]:
                        
                        lineItemId = put_req_paylaod[0]['lineItemId']
                        print(f"updated lineItem Recommednation for Adgroup with id : {lineItemId} with response: {put_req_paylaod}")
                        # lineitem_obj = LineItems.query.filter_by(line_item_id = lineItemId).first()
                        # lineitem_obj. = 
                        # db.session.commit()
                        # print(f"New data for lineitem {lineItemId} Updated in db")

                    updateDB(reco_id, user_action)
                except Exception as e:
                    print("error occured :" , str(e))
                    return Response (f"error occured : {str(e)}", 500)    
         
            
            if lineItem_obj.flag == "DEACTIVATE":
                try:
                    deavtivate_call_response = deactivateLineitems(lineItemId, "INACTIVE")
                    updateDB(reco_id, user_action)
                except Exception as e:
                        print("error occured :" , str(e))
                        return Response (f"error occured : {str(e)}", 500)


            if lineItem_obj.flag == "REPLACE":
                try:    
                    deavtivate_call_response = deactivateLineitems(lineItemId, "INACTIVE")

                    # print("new_lien_item = ", lineItem_obj.recommendation_object)
                    reco_obj_from_db = lineItem_obj.recommendation_object
                    print(reco_obj_from_db, type(reco_obj_from_db))

                    parsed_payload = reco_obj_from_db.replace("True", "true").replace("False", "false")
                    print("parsed_payload =", parsed_payload)

                    order_id = lineItem_obj.order_id
                    line_item_id_array_tuple = createlineitem([json.loads(parsed_payload)], order_id )
                    print("create_call_response 1 = ",line_item_id_array_tuple[0])

                    domain_updation_array =[]
                    creatives_updation_array=[]
                    line_items_activation_status_array = []
                                
                    # Updating Domains
                    if len(line_item_id_array_tuple[1]) != 0:
                        print("Updating Domains")
                        domain_updation_array = updateDefaultDomains(line_item_id_array_tuple[1])
                        print("domain_array :" , domain_updation_array)

                    # Updating Creatives & activating Lineitems
                    if len(line_item_id_array_tuple[2]) != 0:
                        print("Updating Creatives")
                        creatives_updation_array = updateCreativesRecoLineItem(line_item_id_array_tuple[2], lineItem_obj.brand_id)
                        print("Updating Creatives Complete", creatives_updation_array)

                        print("Activating LineItems")
                        line_items_activation_status_array = activateLineitems(line_item_id_array_tuple[0])

                    response_final = {
                        "line_items_POST_call": line_item_id_array_tuple[0],
                        "domains_updation_call": domain_updation_array,
                        "creatievs_association_call": creatives_updation_array,
                        "line_items_activation_call": line_items_activation_status_array,
                        "status": {"statusMessage": "Success", "statusCode": 200},
                    }
                    print(response_final)

                    updateDB(reco_id, user_action)
                    print("Recommendation Status Approved")      
                    # else:
                    #     return Response (f"error occured : Operation Failed to Replace LineItem", 500)

                except Exception as e:
                    print("error occured :" , str(e))
                    return Response (f"error occured : {str(e)}", 500)


            if lineItem_obj.flag == "FLIGHT_UPDATE":
                try:
                    order_update_budget = lineItem_obj.recommendation_object
                    order_update_budget = json.loads(order_update_budget)

                    order_id = lineItem_obj.order_id

                    get_call_repsonse = getcampaigndetailsfromDSP (order_id)
                    # print("updated_payload =",updated_payload)
                    total_budget = get_call_repsonse["budget"]["totalBudgetAmount"]
                    get_call_repsonse["budget"] = order_update_budget
                    get_call_repsonse["budget"]["totalBudgetAmount"]= total_budget
                    updated_payload = get_call_repsonse

                    flight_update_response = updatecamapigncall(updated_payload)
                    print("flight_update_response = ",flight_update_response)
                    
                    if flight_update_response[0] and 'orderId' in flight_update_response[0]:
                        updateDB(reco_id, user_action)
                    else:
                        return Response (f"error occured : Operation Failed to Approve Recommendation", 500)       

                except Exception as e:
                    print("error occured :" , str(e))
                    return Response (f"error occured : {str(e)}", 500)


        response["status"] = {
            "statusMessage": "Recommendation Approved As Per your request",
            "statusCode" : 200
        }
        return response
    except Exception as e:
        logger.error(str(e))
        error_message = {"Approve/Deny Recommendation status:": "Failed", "error": str(e)}
        print(error_message)
        raise Exception(error_message)

   

'''
# print("new_lien_item = ", lineItem_obj.recommendation_object)
reco_obj_from_db = lineItem_obj.recommendation_object
print(reco_obj_from_db, type(reco_obj_from_db))

parsed_payload = reco_obj_from_db.replace("True", "true").replace("False", "false")
print("parsed_payload =", parsed_payload)

print(parsed_payload[0], parsed_payload[1])
# json_string = parsed_payload[0].replace('\\"', '"')
cleaned_data = parsed_payload.replace("'", "")
print(cleaned_data, type(cleaned_data))

cleaned_data = cleaned_data.strip()[1:-1]
json_string = json.dumps(cleaned_data)
print("JSON STRING = ", json_string)

# Parse the JSON string into a dictionary
json_object = json.loads(json_string)
print(json_object, type(json_object))


order_id = lineItem_obj.order_id
create_call_response = createlineitem([json.loads(json_object)], order_id )
print("create_call_response 1 = ",create_call_response)

'''   