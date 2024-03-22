from flask import Blueprint, jsonify, session, request
import logging
import requests
import json
from models import Campaign, LineItems, AmazonAPICallLogs
from database import db
from datetime import datetime, date
from settings.config import (
    client_id,
    client_secret,
    profile_id,
    refresh_token,
    advertiser_id,
)
import io
from azure.storage.blob import BlobServiceClient
import pandas as pd
from settings.config import (
    storage_account_name,
    account_access_key,
    sas_token,
    container_name,
    connection_string,
    advertiser_id,
)
import time
import asyncio
from functools import wraps
from flask_login import login_required 
from apis.createCampaignAPIs.getPayloadFunction.getpayloadfunction import get_payload
from apis.emailFunctions import send_email
from io import StringIO
from azure.storage.queue import QueueClient

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

placeorderonamazon_blueprint = Blueprint("placeorderonamazon", __name__)

brand_store = {}
date_format = '%Y-%m-%d %H:%M:%S %Z'

# print(type(client_id), type(profile_id), type(client_secret), type(advertiser_id), type(refresh_token))
Devansh_Email = "devanshp@sigmoidanalytics.com"

class CustomException(Exception):
    def __init__(self, message):
        self.message = message
        self.status_code = 600


def getEmailBody(user_name, orderId):
    body = f''' Hi {user_name},

    Congratulations! The order you just placed on Nautilus is successful and has been assigned orderId = {orderId}. It is now ready to be delivered.

    Please note that the campaign will automatically start on the date you set.

    Thank you for choosing Nautilus. If you have any questions or need further assistance, feel free to reach out to our support team.

    Best regards,
    Nautilus Team (Sigmoid) 
    
    This is a system-generated email. Do not reply!
    '''

    return body


def get_access_token(REFRESH_TOKEN):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
    }
    
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": REFRESH_TOKEN,
        "client_secret": client_secret,
    }
    # print(data)
    # print(type(client_id), type(profile_id), type(client_secret), type(advertiser_id), type(refresh_token))

    response = requests.post(
        "https://api.amazon.com/auth/o2/token", headers=headers, data=data
    )
    # print("accesstokenresponse :", response)
    r_json = response.json()
    print("\n Received access token \n")
    return r_json["access_token"]


def placeCampaignOrder(output_payload, input_payload, user_email):
    try:   
            ACCESS_TOKEN = get_access_token(refresh_token)
            url = "https://advertising-api.amazon.com/dsp/orders/"
            payload = [
                {
                    "advertiserId": advertiser_id,
                    "externalId": output_payload["orderPONumber"],
                    "name": output_payload["name"],
                    "budget": output_payload["budget"],
                    "frequencyCap": output_payload["frequencyCap"],
                    "optimization": output_payload["optimization"],
                }
            ]
            data = json.dumps(payload, default=list)
            headers = {
                "Amazon-Advertising-API-ClientId": client_id,
                "Amazon-Advertising-API-Scope": profile_id,
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ACCESS_TOKEN}",
                "Accept": "application/vnd.dsporders.v2.3+json",
            }
            # print(headers)

            response = requests.request("POST", url, headers=headers, data=data)
            response_json = response.json()
            print(response_json)

            if "errorDetails" in response_json[0]:
                error_details = response_json[0]["errorDetails"]
                error_message = f"Error in placeCampaignOrder: {error_details}"
                raise Exception(error_message)

            else:
                campaign_data = Campaign(
                    order_id=response_json[0]["orderId"],
                    campaign_name=output_payload["name"],
                    target_platform_id=1,
                    campaign_type_id=1,
                    brand_id=input_payload["brand"]["id"],
                    region_id=input_payload["region"]["id"],
                    goal_goal_kpi_id=input_payload["goal"]["id"],
                    goal_kpi=input_payload["goalKPI"],
                    context_list=input_payload["contexts"],
                    product_tracking_list=input_payload["product_tracking_list"]["fileName"],
                    start_time=input_payload["startDate"],
                    end_time=input_payload["endDate"],
                    audience_ids=input_payload["audienceIds"],
                    total_budget=input_payload["totalBudget"],
                    max_change_in_budget=input_payload["maxChangeInBudget"],
                    campaign_status="INITIALIZING",
                    created_by_email=user_email,
                    orderPO_number=input_payload["orderPONumber"],
                    domain_names=input_payload["domainNames"],
                    suggestions=input_payload["suggestion"],
                    order_budget=output_payload["budget"],
                    frequency_cap=output_payload["frequencyCap"],
                    budget_optimization=output_payload["optimization"],
                    request_id = output_payload['requestId']
                )
                db.session.add(campaign_data)
                db.session.commit()
                return response_json[0]["orderId"]

    except Exception as e:
        logger.error(str(e))
        print("Inside Place Campaign Order, Error occured : " + str(e))
        return None


def updateProductTrackingList(orderId, output_payload, input_payload):
    try:
        default_flag = output_payload["product_tracking_list"]["defaultSelected"]

        url = f"https://advertising-api.amazon.com/dsp/orders/{orderId}/conversionTracking/products"
        ACCESS_TOKEN = get_access_token(refresh_token)
        headers = {
            "Amazon-Advertising-API-ClientId": client_id,
            "Amazon-Advertising-API-Scope": profile_id,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "Accept": "application/vnd.dspproducttracking.v1+json",
        }

        directory_name = output_payload["name"]
        file_name = output_payload["product_tracking_list"]["fileName"]

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        if default_flag:
            brand_name = input_payload["brand"]["name"]
            blob_name = f"ProductTrackingLists/DEFAULT/{brand_name}/{file_name}"
        else:
            blob_name = f"ProductTrackingLists/{directory_name}/{file_name}"

        blob_client = container_client.get_blob_client(blob_name)
        blob_data = blob_client.download_blob().readall()

        file_stream = io.BytesIO(blob_data)
        df = pd.read_csv(file_stream)
        json_data = []
        for col, row in df.iterrows():
            dict = {}
            dict["productId"] = row["Asin"]
            dict["productAssociation"] = "FEATURED"
            dict["domain"] = "AMAZON_US"
            json_data.append(dict)

        payload = {"productList": json_data}

        response = requests.request("PUT", url, headers=headers, json=payload)

        if response.status_code != 204:
            error_message = f"Error in updateProductTrackingList: {response.json()}"
            raise CustomException(error_message)

        else:
            return "PRODUCT LIST ASSOCIATED SUCCESSFULLY"

    except Exception as e:
        logger.error(str(e))
        return {"error": str(e)}


def updateDomainListPerLineItem(lineItemIdArray, output_payload):
    try:
        default_flag = output_payload["domainNames"]["defaultSelected"]
        domain_updation_array = []

        for line_item_id in lineItemIdArray:
            url = "https://advertising-api.amazon.com/dsp/targeting/domain"

            file_name = "default_domain_list.csv"
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(container_name)

            if default_flag:
                blob_name = f"DomainLists/DEFAULT/{file_name}"
            else:
                camp_name = output_payload["name"]
                blob_name = f"DomainLists/{camp_name}/{file_name}"

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
                    "domainLists": [
                        item["domain_id"]
                        for item in output_payload["domainNames"]["domianIds"]
                    ],
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


def readCreativesintoDF(brand_name):
    try:
        directory_name = brand_name
        file_name = f'{brand_name.lower()}' +'_default_creatives_list.csv'

        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        blob_name = f"CreativesFiles/DEFAULT/{directory_name}/{file_name}"

        blob_client = container_client.get_blob_client(blob_name)
        blob_data = blob_client.download_blob().readall()

        file_stream = io.BytesIO(blob_data)
        df = pd.read_csv(file_stream)

        if df is None:
            raise FileNotFoundError(f"File {file_name} not found in the specified container.")

        return df

    except FileNotFoundError as fnfe:
        print(fnfe)
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    
def updateCreativesperLineItem(ContextlineItemIdMappingArray, input_payload):
    try:

        brand_name = input_payload["brand"]["name"]
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


def activateLineitems(lineItemIdArray):
    lineItemActivationArray = []
    for lineItemId in lineItemIdArray:
        try:
            url = f"https://advertising-api.amazon.com/dsp/lineItems/{lineItemId}/deliveryActivationStatus"

            headers = {
                "Amazon-Advertising-API-ClientId": client_id,
                "Amazon-Advertising-API-Scope": profile_id,
                # "Content-Type": "application/json",
                "Authorization": f"Bearer {get_access_token(refresh_token)}",
                "Accept": "application/vnd.dsplineitemsdeliveryactivationstatus.v3+json",
            }

            params = {"status": "ACTIVE"}
            # params = {"status": "INACTIVE"}

            response = requests.request("POST", url, headers=headers, params=params)


            while(response.status_code != 204 and 'message' in response.json() and response.json()['message'] == 'Too Many Requests'):
                print("Retrying for 'Too many request error' ERROR after 5 sec")
                time.sleep(5)
                response = requests.request("POST", url, headers=headers, params=params)
               

            if response.status_code != 204:
                error_message = f"Error in activatinglineItem {lineItemId}: {response.json()}"
                print("error:" +  error_message, response.json())
                lineItemActivationArray.append(f"LineItem with id: {lineItemId} ACTIVATION FAILED")
                raise Exception(error_message)

            else:
                print (f"LineItem with {lineItemId} ACTIVATED SUCCESSFULLY")
                lineItemActivationArray.append(f"LineItem with id: {lineItemId} ACTIVATED SUCCESSFULLY")
                

        except Exception as e:
            # logger.error(str(e))
            print({"LineItems Activation status": "FAILED", "error": str(e)})
            return jsonify({"LineItems Activation status": "FAILED", "error": str(e)})

    print(lineItemActivationArray)
    return lineItemActivationArray


def makeLineItemCalls(orderId, output_payload):
    line_item_id_array = []
    SD_line_item_ID_array = []
    creatives_line_mapping_array = []
    try: 
        for line_item in output_payload["lineitems"]:
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

            # if (
            #         "errorDetails" in response_json[0]
            #         and (
            #             response_json[0]["errorDetails"]["errors"][0]["errorType"] == "INVALID_SEGMENT_TARGETING_SEGMENT_ID"
            #         or  response_json[0]["errorDetails"]["errors"][0]["errorType"] == "UNSUPPORTED_AUDIENCE_SEGMENTS"
            #         )
            #     ):                  
            #     task_name = f"Issue Encountered while creating campaign {orderId}"
            #     error_message = f"{response_json[0]['errorDetails']['errors'][0]['message']}"
            #     body = f"Line Item Failed to Create due to Unsupported Audience id isssue. \nError = {error_message}"

            #     if send_email(session["okta_attributes"]['email'], task_name, body):
            #         print("Email sent successfully to the user for line item error.")
            #     else:
            #         print("Email sending failed due to issue on Azure Logic Gates.")


            while('message' in response_json and response_json['message'] == 'Too Many Requests'):
                print("Retrying for 'Too many request error' ERROR")
                time.sleep(5)
                response = requests.request("POST", url, headers=headers, data=payload_str)
                response_json = response.json()


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
                print(f"Request failed with status code: {response.status_code}")
                # return jsonify({f"Request failed with status code: {response.status_code}"})

        return (line_item_id_array, SD_line_item_ID_array,creatives_line_mapping_array )

    except Exception as e:
        logger.error(str(e))
        print("error in line items:", str(e))
        error_message = f"No line items were created for orderId: {orderId}. Error in line items: {str(e)}"
        response = jsonify({"error": error_message})
        response.status_code = 500  # Internal Server Error
        return response


def activateOrder(orderId):
    try:
        url = f"https://advertising-api.amazon.com/dsp/orders/{orderId}/deliveryActivationStatus"

        headers = {
            "Amazon-Advertising-API-ClientId": client_id,
            "Amazon-Advertising-API-Scope": profile_id,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {get_access_token(refresh_token)}",
            "Accept": "application/vnd.dsporders.v2.2+json",
        }

        params = {"status": "ACTIVE"}
        # params = {"status": "INACTIVE"}

        response = requests.request("POST", url, headers=headers, params=params)

        while(response.status_code != 204 and 'message' in response.json() and response.json()['message'] == 'Too Many Requests'):
            print("Retrying for 'Too many request error' ERROR after 5 sec")
            time.sleep(5)
            response = requests.request("POST", url, headers=headers, params=params)

        if response.status_code != 204:
            error_message = f"Error in activateOrder: {response.json()}"
            print("error:" +  error_message, response.json())
            raise Exception(error_message)

        else:
            print ("ORDER ACTIVATED SUCCESSFULLY")
            return "ORDER ACTIVATED SUCCESSFULLY"
            

    except Exception as e:
        logger.error(str(e))
        return jsonify({"status": "FAILED", "error": str(e)})


def placeOrderOnAmazonExe(msg):
        try:
            input_payload = msg["content"]
            print("input_payload",input_payload)
            print( type(input_payload) )
            json_str = input_payload.replace("'", "\"")
            json_str = json_str.replace("True", "true").replace("False", "false")
            print("json_str",json_str)
            input_payload = json.loads(json_str)
            print( type(input_payload) )
            userName = input_payload["user_name"]
            userEmail = input_payload["user_email"]
            input_payload.pop("user_name", None)
            input_payload.pop("user_email", None)

            output_payload = get_payload(input_payload)
            if output_payload != None:
                print("Output paylaod recieved Successfully")
            print(output_payload)

            task_name = f"Campaign Payload Generated"
            body =  f"Campaign Payload Generated \n: {output_payload} for campaign Creation Request by {userName}"
            if send_email(Devansh_Email, task_name, body):
                print(f"Email sent successfully to Devansh with payload used in Campaign Creation by user {userEmail}")
            else:
                print("Email sending failed due to issue on Azure Logic Gates.")
                
            
            # Placing Campaign Order 
            print("Placing Order")
            orderId = placeCampaignOrder(output_payload, input_payload, userEmail)
            if orderId is None:
                raise Exception ("Error in Placing order function")
            print ("Order Placed Successfully with OrderID", orderId)


            # Associating Product List
            print("Updating Product List")
            update_product_list_response = updateProductTrackingList(orderId, output_payload, input_payload)
            if "error" in update_product_list_response:
                if orderId:
                    camp_obj = Campaign.query.filter_by(order_id = orderId).first()
                    camp_obj.campaign_status = "FAILED"
                    db.session.commit()
                error_message = f"Order Placed for orderId: {orderId}, but Product List association failed"
                response = jsonify({"error": error_message, "details": update_product_list_response["error"]})
                response.status_code = 600  # Internal Server Error
                return response
            print(f"Product_list_associated_successfully for orderId = {orderId}", update_product_list_response)


            # Placing Line Item Calls
            print("Placing Line Item calls")
            line_item_id_array_tuple = makeLineItemCalls(orderId, output_payload)
            print(f"LineItems array for orderId = {orderId}", line_item_id_array_tuple[0])


            domain_updation_array =[]
            creatives_updation_array=[]
            line_items_activation_status_array = []
            
            # Updating Domains
            if len(line_item_id_array_tuple[1]) != 0:
                print("Updating Domains")
                domain_updation_array = updateDomainListPerLineItem(line_item_id_array_tuple[1], output_payload)
                # print("domain_array :" , domain_updation_array)

            # Updating Creatives & activating Lineitems
            if len(line_item_id_array_tuple[2]) != 0:
                print("Updating Creatives")
                creatives_updation_array = updateCreativesperLineItem(line_item_id_array_tuple[2], input_payload)
                # print("Updating Creatives Complete", creatives_updation_array)

                print("Activating LineItems")
                line_items_activation_status_array = activateLineitems(line_item_id_array_tuple[0])

            # Activating Order
            activation_status_response = activateOrder(orderId)
            if "error" in activation_status_response:
                error_message = "An error occurred while activation But order is placed"
                response = jsonify({"error": error_message})
                response.status_code = 500  # Internal Server Error
                return response
            print ("Activation Status:" , activation_status_response)


            response_final = {
                "campaign_order_call": orderId,
                "product_list_updation_call": update_product_list_response,
                "line_items_POST_call": line_item_id_array_tuple[0],
                "domains_updation_call": domain_updation_array,
                "creatievs_association_call": creatives_updation_array,
                "line_items_activation_call": line_items_activation_status_array,
                "order_activation_call": activation_status_response,
                "status": {"statusMessage": "Success", "statusCode": 200},
            }
            # print(response_final)
            
            # Update campaign status to "READY TO DELIVER"
            camp_obj = Campaign.query.filter_by(order_id = orderId).first()
            camp_obj.campaign_status = "READY TO DELIVER"
            db.session.commit()
            print("Changed campaign Status to 'READY TO DELIVER' ")


            # SEND MAIL TO USER
            task_name = f"Campaign ({orderId}) is READY TO DELIVER on Amazon DSP"
            body = getEmailBody (userName, orderId)

            if send_email(userEmail, task_name, body):
                print("Email sent successfully to the user.")
            else:
                print("Email sending failed due to issue on Azure Logic Gates.")

            # PUT API LOGS INTO DB
            try:
                amazon_api_log = AmazonAPICallLogs (user_email= userEmail, payload = output_payload, response = response_final)
                db.session.add(amazon_api_log)
                db.session.commit()
                print("API logs inserted into DB successfully")
                
            except Exception as e:
                print("Error in updating API logs into DB.....error:" + str(e))

            return jsonify(response_final)

        except Exception as e:
            logger.error(str(e))
            flag = 0 
            if orderId:
                camp_obj = Campaign.query.filter_by(order_id = orderId).first()
                camp_obj.campaign_status = "FAILED"
                db.session.commit()
            
                task_name = f"Campaign Creation Failed"
                body =  f"Campaign with {orderId} is Failed to Create on Amazon DSP due to error: {str(e)}"
                if send_email(userEmail, task_name, body):
                    flag =1
                    print("Email sent successfully to the user informing campaign creation failed")
                else:
                    print("Email sending failed due to issue on Azure Logic Gates.")  


            if flag == 0:
                task_name = f"Campaign Creation Failed"
                body =  f"Campaign Failed to Create on Amazon DSP due to error: {str(e)}"
                if send_email(userEmail, task_name, body):
                    print("Email sent successfully to the user informing campaign creation failed")
                else:
                    print("Email sending failed due to issue on Azure Logic Gates.")

            error_message = "An error occurred in major API: " + str(e)
            response = jsonify({"error": error_message})
            response.status_code = 500  # Internal Server Error
            print(response)
            return response



@placeorderonamazon_blueprint.route("/placeorderonamazon", methods=["POST"])
def placeOrderOnAmazon():
    try:
        input_payload = request.json
        input_payload["user_name"] = session['okta_attributes']['given_name']
        input_payload["user_email"] = session['okta_attributes']['email']

        queue_client = QueueClient(account_url=f"https://{storage_account_name}.queue.core.windows.net", queue_name="amc-queue",credential=account_access_key)
        queue_client.send_message(input_payload)
        print("Payload added in the queue")
        return {"status": {"statusMessage": "Your campaign request has been accepted. You will receive email notification about status of your request", "statusCode": 202}}, 202

    except Exception as e:
        return {"error": str(e)}, 500