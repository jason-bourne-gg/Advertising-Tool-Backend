from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import OrderPONumber
from sqlalchemy.sql import extract
from database import db


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

orderPOnumber_blueprint = Blueprint('orderPOnumber', __name__)

orderPOnumber_store = {}

@orderPOnumber_blueprint.route('/getorderPOnumber', methods=['GET'])
@login_required
def getorderPOnumber():
    try:
        data_obj_list = OrderPONumber.query.all()
        # print(data_obj_list)
        data = []
        for item_obj in data_obj_list:
            dict = {}
            dict["id"] = item_obj.id
            dict["order_PO_numbers"] = item_obj.orderPOnumber
            dict["is_default"] = item_obj.is_default

            data.append(dict)

        response = {}
        response['data'] = data
        response["status"] = {
            "statusMessage": "Success",
            "statusCode" : 200
        }
        return response 

    except Exception as e:
        response = {}
        response["data"] = []
        status = {
                    "statusCode": 500,
                    "statusMessage": f"Could not fetch list of PO numbers", 
                    "error": str(e)
                  }
        response["status"] = status
        logger.debug(response)
        return response, 500  

@orderPOnumber_blueprint.route('/getdefaultponumber', methods=['GET'])
@login_required
def getdefaultponumber():
         
    default_PO_obj = OrderPONumber.query.filter_by(is_default = "TRUE").first()

    # print(default_PO_obj)
    # data = []
    dict = {}
    if default_PO_obj:
        dict["order_PO_number"] = default_PO_obj.orderPOnumber

    # data.append(dict)

    response = {}
    response['data'] = dict
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    #logger.debug(response)
    return response  


@orderPOnumber_blueprint.route('/makedefaultponumber', methods=['POST'])
@login_required
def makedefaultponumber():
    try:     
        request_data = request.json
        PO_num = request_data["orderPOnumber"]

        # Make existing PO number as NOT DEFAULT
        exitsing_default_PO_obj = OrderPONumber.query.filter_by(is_default = "TRUE").first()
        if exitsing_default_PO_obj:
            exitsing_default_PO_obj.is_default = "FALSE"
            db.session.commit()  

        # makeing given PO num as Default
        new_default_PO_obj = OrderPONumber.query.filter_by(orderPOnumber = PO_num).first()
        if new_default_PO_obj:
            new_default_PO_obj.is_default = "TRUE"
            db.session.commit() 

        response = {}
        response["status"] = {
            "statusMessage": f"{PO_num} has been set as default PO Number Successfully",
            "statusCode" : 200
        }
        return response  
    
    except Exception as e:
        response = {}
        response["data"] = {}
        status = {
                    "statusCode": 500,
                    "statusMessage": f"Could not set {PO_num} as Default Order PO Number", 
                    "error": str(e)
                  }
        response["status"] = status

        logger.debug(response)
        return response, 500    
    # logger.debug(response)

 
@orderPOnumber_blueprint.route('/postorderPOnumber', methods=['POST'])
@login_required 
def postOrderPOnumber():
    request_data = request.json
    print(request_data)
    array_of_PO_nums = request_data["order_PO_numbers"]

    for num in array_of_PO_nums:
        PO_num = OrderPONumber(orderPOnumber = num, is_default = "FALSE")
        db.session.add(PO_num)
        db.session.commit()  

    response = {}
    response['data'] = "Order PO Numbers has been successfully updated in database"
    response["status"] = {
        "statusMessage": "Success",
        "statusCode" : 200
    }
    #logger.debug(response)
    return response      



@orderPOnumber_blueprint.route('/deleteorderPOnumber', methods=['DELETE'])
@login_required
def deleteOrderPOnumber():
    request_data = request.json
    print(request_data)
    po_number_to_delete = request_data["order_PO_number"]

    # Retrieve the PO number object from the database
    PO_num = OrderPONumber.query.filter_by(orderPOnumber=po_number_to_delete).first()

    if PO_num:
        # Delete the PO number from the database
        db.session.delete(PO_num)
        db.session.commit()
        return {"message": f"PO number '{po_number_to_delete}' deleted successfully."}, 200
    else:
        return {"message": f"PO number '{po_number_to_delete}' not found in the database."}, 404
