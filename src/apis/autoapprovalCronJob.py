from flask import Flask, Response
from database import db
from flask_apscheduler import APScheduler
from settings.config import *
from models import CampaignRecommendations
from datetime import datetime, timezone, timedelta
from apis.currentCampaignAPIs.approveordenyreco import (
    getcampaigndetailsfromDSP,
    getlineItemDetailsfromDSP,
    createlineitem,
    update_payload,
    updatecamapigncall,
    updateLineItemData,
    updateDB,
    deactivateLineitems,
    updateDefaultDomains,
    updateCreativesRecoLineItem
)
from apis.createCampaignAPIs.placeorderamazonAPI import activateLineitems
from app import app


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def my_cron_job():
    print("Running my_cron_job")
    with app.app_context():
    # Calculate the date range (3 days ago from today)
        today = datetime.now(timezone.utc).date()
        three_days_ago = today - timedelta(days=3)

        recosToBeApproved = CampaignRecommendations.query.filter(
            CampaignRecommendations.date_of_generation < three_days_ago,
            CampaignRecommendations.status == 'PENDING'
        ).all()
        if len(recosToBeApproved) == 0:
            print (f"No Recommendation generated from past 3 days..NOTHING to approve on date: {datetime.utcnow()}!")
        else :
            print(f"Recommendations to be approved on {today}:", recosToBeApproved)


        for reco in recosToBeApproved:
            lineItemId = reco.line_item_id
            print(f"Operation to be performed on Recommendation of lineitemid: {lineItemId}", reco.flag)

            if reco.flag == None:
                print(f"Could Not find operation to perform on lineitem {lineItemId}")
                continue  # Continue to the next iteration of the loop

            if reco.flag == "UPDATE":
                try:
                    getCallResponse = getlineItemDetailsfromDSP (lineItemId)
                    if 'message' in getCallResponse:
                        print("Error in fetching details from Amazon")
                        return Response (f"Error in fetching details from Amazon", 500)  

                    reco_obj = reco.recommendation_object
                    order_id = reco.order_id
                    updated_payload = update_payload(getCallResponse, json.loads(reco_obj))
                    # print(updated_payload)

                    put_req_paylaod = updateLineItemData(updated_payload)

                    if 'lineItemId' in put_req_paylaod[0]:
                        
                        lineItemId = put_req_paylaod[0]['lineItemId']
                        print(f"updated lineItem Recommednation for Adgroup with id : {lineItemId} with response: {put_req_paylaod}")
                        # reco = LineItems.query.filter_by(line_item_id = lineItemId).first()
                        # reco. = 
                        # db.session.commit()
                        # print(f"New data for lineitem {lineItemId} Updated in db")

                    updateDB(reco.id, "APPROVED")
                except Exception as e:
                    print("error occured :" , str(e))
                    continue  # Continue to the next iteration of the loop
        
            
            if reco.flag == "DEACTIVATE":
                try:
                    deavtivate_call_response = deactivateLineitems(lineItemId, "INACTIVE")
                    updateDB(reco.id, "APPROVED")
                except Exception as e:
                    print("error occured :" , str(e))
                    continue  # Continue to the next iteration of the loop


            if reco.flag == "REPLACE":
                try:    
                    deavtivate_call_response = deactivateLineitems(lineItemId, "INACTIVE")

                    # print("new_lien_item = ", reco.recommendation_object)
                    reco_obj_from_db = reco.recommendation_object
                    # print(reco_obj_from_db, type(reco_obj_from_db))

                    parsed_payload = reco_obj_from_db.replace("True", "true").replace("False", "false")
                    # print("parsed_payload =", parsed_payload)

                    order_id = reco.order_id
                    line_item_id_array_tuple = createlineitem([json.loads(parsed_payload)], order_id )
                    print("create_call_response 1 = ",line_item_id_array_tuple[0])

                    if len(line_item_id_array_tuple[0]) == 0 :
                        raise Exception("Could not place-order for new line item")

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
                        creatives_updation_array = updateCreativesRecoLineItem(line_item_id_array_tuple[2], reco.brand_id)
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

                    updateDB(reco.id, "APPROVED")
                    print("Recommendation Status Approved")      
                    # else:
                    #     return Response (f"error occured : Operation Failed to Replace LineItem", 500)

                except Exception as e:
                    print("error occured :" , str(e))
                    continue  # Continue to the next iteration of the loop


            if reco.flag == "FLIGHT_UPDATE":
                try:
                    order_update_budget = reco.recommendation_object
                    order_update_budget = json.loads(order_update_budget)

                    order_id = reco.order_id

                    get_call_repsonse = getcampaigndetailsfromDSP (order_id)
                    # print("updated_payload =",updated_payload)
                    total_budget = get_call_repsonse["budget"]["totalBudgetAmount"]
                    get_call_repsonse["budget"] = order_update_budget
                    get_call_repsonse["budget"]["totalBudgetAmount"]= total_budget
                    updated_payload = get_call_repsonse

                    flight_update_response = updatecamapigncall(updated_payload)
                    print("flight_update_response = ",flight_update_response)

                    if flight_update_response[0] and 'orderId' in flight_update_response[0]:
                        updateDB(reco.id, "APPROVED")
                    else:
                        print (f"error occured : Operation Failed to Approve Recommendation")       

                except Exception as e:
                    print("error occured :" , str(e))
                    continue  # Continue to the next iteration of the loop          

        logging.info("Cron job executed successfully.")
        print(f"Cron job executed successfully for {datetime.utcnow()}.")

