from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import Suggestion
from sqlalchemy.sql import extract


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

suggestions_blueprint = Blueprint('suggestions', __name__)

suggestions_store = {}

@suggestions_blueprint.route('/getsuggestions', methods=['GET', 'POST'])
@login_required
def getSuggestions():
    request_data = request.json
    # print(request_data)
    brandid = request_data["brand"]["id"]
    # regionid = request_data["region"]["id"] 
    context_array = request_data['contexts']

    data_obj_list = Suggestion.query.filter(Suggestion.brand_id == brandid, Suggestion.context.in_(context_array) ).all()
    # print(data_obj_list)

    def getContextArray ():
        array = []
        for suggestions_obj in data_obj_list :
            tup = {f'{suggestions_obj.context}' : suggestions_obj.bid }
            array.append(tup)

        return array

    data = []
    data_obj = Suggestion.query.filter_by(brand_id= brandid ).first()
    # print (data_obj)
    dict={}
    dict["brand"] = data_obj.brand.brand_name
    dict["region"] = data_obj.region.region_name
    dict["context: bid"] = getContextArray()
    dict["viewability"] = data_obj.viewability
    dict["frequency_cap_days"] = data_obj.frequency_cap_days
    dict["frequency_cap_amount"] = data_obj.frequency_cap_amount
    # print(dict)
    data.append(dict)
    # print(data)
       

    # data= {}
    response = {}
    response['data'] = data
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    #logger.debug(response)
    return response    
 
    