from flask import Blueprint, jsonify,session,redirect
import logging
from flask_login import login_required 
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__,BlobSasPermissions,generate_blob_sas
from datetime import datetime, timedelta
import os,uuid
from settings.config import storage_account_name,account_access_key,sas_token,container_name, connection_string
import json
from azure.core.exceptions import AzureError



# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

creativesfile_blueprint = Blueprint('creativesfile_blueprint', __name__)

creativesfile_store = {}

@creativesfile_blueprint.route('/uploadcreativesfile', methods=['POST'])
@login_required
def uploadCreativesFile():
    if 'file_to_be_uploaded' not in request.files:
        return jsonify({'error': 'No file found in the request'}), 400

    csv_file = request.files['file_to_be_uploaded']
    # print (request.files['file_to_be_uploaded'])
    if csv_file.filename == '':
        return jsonify({'error': 'Filename cannot be empty'}), 400
    print(csv_file.filename)

    request_data = request.form
    directory_name = request_data.get("brand")
    # directory_name = json.loads(brand_obj)["name"]
    if not directory_name:
        return jsonify({'error': 'No brand name provided in request'}), 400
    print(directory_name)

    custom_file_name = f'{directory_name.lower()}' +'_default_creatives_list'

    try:
        # connect to azure blob & get ref to container
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)


        #design unique name for blob 
        blob_name = f'CreativesFiles/DEFAULT/{directory_name}/' + custom_file_name + ".csv"

        # Check if the blob exists and delete it if it does
        if container_client.get_blob_client(blob_name).exists():
            container_client.delete_blob(blob_name)

        # uploading blob   
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(csv_file)

        return jsonify({"message": "Creatives File uploaded successfully!"}), 200
    
    except AzureError as azure_error:
        error_message = "Azure error: File you have selected already exist in the azure storage " 
        return jsonify({"error": error_message}), 500

    except Exception as e:
        error_message = "Unknown error occurred: " + str(e)[:40]
        return jsonify({"error": error_message}), 500
    


@creativesfile_blueprint.route('/downlaodcreativesfile', methods=['POST'])
@login_required
def downloadCreativesList():
    try:
        directory_name = request.json["brand"]['name']
        if not directory_name:
            return jsonify({'error': 'No Brand name provided'}), 400
        # print(directory_name)

        file_name = f'{directory_name.lower()}' +'_default_creatives_list.csv'

        # Create a connection to Azure Blob Storage & Get a reference to the container
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_name = f'CreativesFiles/DEFAULT/{directory_name}/{file_name}'
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