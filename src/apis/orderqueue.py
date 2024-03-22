from flask import Blueprint, jsonify, session, request,current_app
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
from apis.createCampaignAPIs.placeorderamazonAPI import placeOrderOnAmazonExe
from azure.storage.queue import QueueClient
from app import app


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)



def execute_queue():
    try:
        with app.app_context():
            print("\nRUNNING EXECUTION")
            queue_client = QueueClient(account_url=f"https://{storage_account_name}.queue.core.windows.net", queue_name="amc-queue",credential=account_access_key)
            try:
                message = queue_client.receive_message(visibility_timeout= 9000) #30 min invisibility to next run
                
                if message is not None:
                    print("msg: ", message)
                    # "Process" the message
                    print("Start message processing: {}, start time: {}".format(message.content, datetime.utcnow()))
                    response = placeOrderOnAmazonExe (message)    
                    print(response)
                    print("End message processing: {}, end time: {}".format(message.content, datetime.utcnow()))
                    
                    # Let the service know we're finished with the message and it can be safely deleted.
                    queue_client.delete_message(message)
                    print("Message deleted successfully: ", message.content)

                else :
                    print("Currently nothing in queue to execute")
            
            except Exception as e:
                print("No Messages in Queue: ", str(e))
                return {"error": str(e)}

    except Exception as e:
        print("Failed to load queue client: ", str(e))
        return {"error": str(e)}