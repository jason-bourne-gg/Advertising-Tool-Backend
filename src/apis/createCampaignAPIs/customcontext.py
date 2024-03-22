from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import CustomContext
from sqlalchemy.sql import extract


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

customcontext_blueprint = Blueprint('customcontext', __name__)

customcontext_store = {}

@customcontext_blueprint.route('/getcustomcontext', methods=['GET'])
# @login_required
def getCustomContext():

    data_obj_list = CustomContext.query.all()
    # print(data_obj_list)
    data = []
    
    for item_obj in data_obj_list:
        # print (item_obj)
        dict={}
        dict["line_item_type"] = item_obj.line_item_type
        dict["device_type"] = item_obj.device_type
        dict["supply_source"] = item_obj.supply_source
      
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
 
    