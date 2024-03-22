from flask import Blueprint, jsonify,session,redirect,send_file,make_response
import logging
from flask_login import login_required 
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__,BlobSasPermissions,generate_blob_sas
from datetime import datetime, timedelta
import os,uuid
from settings.config import storage_account_name,account_access_key,sas_token,container_name, connection_string



# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

downloadproducttrackinglist_blueprint = Blueprint('downloadproducttrackinglist', __name__)

downloadproducttrackinglist_store = {}

@downloadproducttrackinglist_blueprint.route('/downloadproducttrackinglist', methods=['POST', 'GET'])
@login_required
def downloadProductTrackingList():
    try:
        directory_name = request.json["campaign_name"]
        if not directory_name:
            return jsonify({'error': 'No campaign name provided'}), 400
        # print(directory_name)

        file_name = request.json["file_name"]
        if not file_name:
            return jsonify({'error': 'No file name provided'}), 400
        # print(file_name)

        # Create a connection to Azure Blob Storage & Get a reference to the container
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_name = f'ProductTrackingLists/{directory_name}/{file_name}'
        blob_client = container_client.get_blob_client(blob_name)
        
        if not blob_client.exists():
            return jsonify({'error': 'File not found'}), 404
        
    
        sas_token2 = generate_blob_sas(
        account_name=storage_account_name,
        account_key=account_access_key,
        container_name=container_name,
        blob_name= blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)  # Expiry time: 1 hour from now
        )

        # print(sas_token2)

        download_url = blob_client.url + '?' + sas_token2

        return jsonify({'download_url': download_url, 'statusMessage':"Success"})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500