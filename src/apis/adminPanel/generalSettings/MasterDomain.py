from flask import Blueprint, jsonify,session,redirect
import logging
from flask_login import login_required 
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
from datetime import datetime, timedelta
import os,uuid
from azure.storage.blob import BlobServiceClient,BlobSasPermissions,generate_blob_sas
from azure.core.exceptions import AzureError
from settings.config import storage_account_name,account_access_key,sas_token,container_name, connection_string

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

masterdomainlist_blueprint = Blueprint('masterdomainlist_blueprint', __name__)

masterdomainlist_store = {}

@masterdomainlist_blueprint.route('/uploadmasterdomainlist', methods=['POST'])
@login_required
def downloadmasterDomainList():

    if 'file_to_be_uploaded' not in request.files:
        return jsonify({'error': 'No file found in the request'}), 400

    csv_file = request.files['file_to_be_uploaded']
    # print (request.files['file_to_be_uploaded'])
    if csv_file.filename == '':
        return jsonify({'error': 'Filename Cannot be empty'}), 400
    print(csv_file.filename)

    # request_data = request.form
    # directory_name = request_data.get("campaign_name")
    # if directory_name is None:
    #     return jsonify({'error': 'No campaign name provided in the request'}), 400
    # print(directory_name)

    custom_file_name = f'default_domain_list'

    try:
        # connect to azure blob & get ref to container
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)

        #design unique name for blob 
        blob_name = f'DomainLists/DEFAULT/' + custom_file_name + ".csv"
        # blob_name = f'DomainLists/DEFAULT/' + str({csv_file}) + ".csv" ..........some error when u use this

        # Check if the blob exists and delete it if it does
        if container_client.get_blob_client(blob_name).exists():
            container_client.delete_blob(blob_name)

        # uploading blob   
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(csv_file)

        return jsonify({"message": "Domains file uploaded successfully!"}), 200

    except AzureError as azure_error:
        error_message = "Azure error: File you have selected already exist in the azure storage " 
        return jsonify({"error": error_message}), 500

    except Exception as e:
        error_message = "Unknown error occurred: " + str(e)[:40]
        return jsonify({"error": error_message}), 500




@masterdomainlist_blueprint.route('/downloadmasterdomainlist', methods=['GET'])
@login_required
def downloadDomainList():
    file_name = 'default_domain_list.csv'
    
    try:
        # Create a connection to Azure Blob Storage & Get a reference to the container
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        blob_name = f'DomainLists/DEFAULT/{file_name}'
        blob_client = container_client.get_blob_client(blob_name)

        if not blob_client.exists():
            return jsonify({'error': 'File not found'}), 404
        
        sas_token2 = generate_blob_sas(
        account_name=storage_account_name,
        account_key=account_access_key,
        container_name=container_name,
        blob_name = blob_name,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)  # Expiry time: 1 hour from now
        )

        # print(sas_token2)

        download_url = blob_client.url + '?' + sas_token2

        return jsonify({'download_url': download_url, 'statusMessage':"Success"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
