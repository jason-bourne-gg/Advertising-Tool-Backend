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

getdefaultproducttrackinglist_blueprint = Blueprint('getdefaultproducttrackinglist', __name__)

getdefaultproducttrackinglist_store = {}

@getdefaultproducttrackinglist_blueprint.route('/getdefaultproducttrackinglist', methods=['POST'])
@login_required
def getdefaultProductTrackingList():
    try:
        directory_name = request.json["brand"]["name"]
        if not directory_name:
            return jsonify({'error': 'No brand name provided'}), 400
        print(directory_name)

        # file_name = "productlist.csv"
        file_name = f'{directory_name.lower()}' +'_default_product_list.csv'

        # Create a connection to Azure Blob Storage & Get a reference to the container
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_name = f'ProductTrackingLists/DEFAULT/{directory_name}/{file_name}'
        print(blob_name)
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

        getdefault_url = blob_client.url + '?' + sas_token2

        return jsonify({'getdefault_url': getdefault_url, 'file_name' : file_name, 'statusMessage':"Success"})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500