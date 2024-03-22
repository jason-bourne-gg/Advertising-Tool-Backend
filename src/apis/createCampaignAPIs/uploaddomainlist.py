from flask import Blueprint, jsonify,session,redirect
import logging
from flask_login import login_required 
from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__
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

uploaddomainlist_blueprint = Blueprint('uploaddomainlist', __name__)

uploaddomainlist_store = {}

@uploaddomainlist_blueprint.route('/uploaddomainlist', methods=['GET', 'POST'])
@login_required
def uploadDomainList():
    
    if request.method == "POST":

        if 'file_to_be_uploaded' not in request.files:
            return jsonify({'error': 'No file found in the request'}), 400
    
        csv_file = request.files['file_to_be_uploaded']
        # print (request.files['file_to_be_uploaded'])
        if csv_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        print(csv_file.filename)
        
        request_data = request.form
        directory_name = request_data.get("campaign_name")
        if directory_name is None:
            return jsonify({'error': 'No campaign name provided'}), 400
        print(directory_name)

        try:
            # connect to azure blob & get ref to container
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(container_name)


            #design unique name for blob 
            blob_name = f'DomainLists/{directory_name}/' + os.path.splitext(csv_file.filename)[0] + ".csv"

            # uploading blob   
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(csv_file)

            return jsonify({"message": "Domains file uploaded successfully!"}), 200
        except Exception as e:
            error_message = str(e)[:50]  # Extract the first 50 characters of the error message
            return jsonify({"error": error_message}), 500



    