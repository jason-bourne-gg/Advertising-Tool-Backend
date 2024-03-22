from flask import request, jsonify, Blueprint
import requests
from database import db 
from models import DummyTable  
import logging
from flask_login import login_required 


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

postbidvalues_blueprint = Blueprint('postbidvalues', __name__)

brand_store = {}

@postbidvalues_blueprint.route('/postbidvalues', methods=['POST'])
# @login_required
def postBidValues():
    request_data = request.json
    context_bid_array = request_data['context: bid']
    # print(context_bid_array)
    
    for item in context_bid_array:
        for key,value in item.items():
            print(key, value)
            '''
            # for key,value in item:
            # key = entry
            # value = item[entry]
            '''
        try:
            # Check if the entry already exists in the database based on the primary key 'recommended_context'
            existing_entry = DummyTable.query.filter_by(recommended_context=key).first()

            if existing_entry:
                # If the entry exists, update its 'user_bid_value' with the new value
                existing_entry.user_bid_value = value
                db.session.commit()
                print(f"Data updated in table for key = {key} & value = {value}")
            else:
                # If the entry does not exist, create a new row in the database
                new_entry = DummyTable(recommended_context=key, user_bid_value=value)
                db.session.add(new_entry)
                db.session.commit()
                print(f"Data inserted into table for key = {key} & value = {value}")

        except Exception as e:
            print("Error in updating API logs into DB.....error:" + str(e))
            raise ("Error in updating API logs into DB.....error:" + str(e), 500)
        
        
    response = {
        "data": "Data inserted successfully into Database",
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
    }

    return response