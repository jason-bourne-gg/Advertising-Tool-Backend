from flask import Blueprint, jsonify,session
import logging
from flask_login import login_required 
from models import ColumnLineItems


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

column_blueprint = Blueprint('column', __name__)

column_store = {}

@column_blueprint.route('/getlineitemscolumnsfilters', methods=['GET'])
@login_required
def getColumns():
    data_obj_list = ColumnLineItems.query.first()
    print(data_obj_list)
    data = []

    # def makearrayofobj(obj):
    #     array = []
    #     for index, item in enumerate(obj):
    #         dict = {}
    #         dict["id"] = index
    #         dict["columnName"] = item
    #         array.append(dict)
    
    #     return array
    
    # dict["Delivery"] = makearrayofobj(column_obj.delivery)
    # dict["Performance"] = makearrayofobj(column_obj.performance)

    dict={}    
    dict["columnFilter"] = "Delivery"
    dict["values"] = data_obj_list.delivery
    # print(dict)
    data.append(dict)
    
    dict={}
    dict["columnFilter"] = "Performance"
    dict["values"] = data_obj_list.performance
    data.append(dict)
    # print(data)
    
    response = {}
    response['data'] = data
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    #logger.debug(response)
    return response    
 
    