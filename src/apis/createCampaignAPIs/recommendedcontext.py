from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import RecommendedContexts
from sqlalchemy.sql import extract


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

recommendedcontext_blueprint = Blueprint('recommendedcontexts', __name__)

recommendedcontext_store = {}

@recommendedcontext_blueprint.route('/getrecommendedcontexts', methods=['GET', 'POST'])
@login_required
def getRecommendedContexts():
    request_data = request.json
    # print(request_data)
    brandid = request_data["brand"]["id"]
    regionid = request_data["region"]["id"]
    # print(brand_id, region_id)
    
    data_obj_list = RecommendedContexts.query.filter_by(brand_id = brandid ,region_id = regionid ).all()
    # print(data_obj_list)
    data = []
    
    for item_obj in data_obj_list:
        # print (item_obj)
        dict={}
        dict["context"] = item_obj.context
        dict["brand"] = item_obj.brand.brand_name
        # dict["region"] = item_obj.region.region_name
    
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
 
    