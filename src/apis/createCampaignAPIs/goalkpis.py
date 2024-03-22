from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import GoalGoalKPI
from sqlalchemy.sql import extract


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

goalkpis_blueprint = Blueprint('goalkpis', __name__)

goalkpis_store = {}

@goalkpis_blueprint.route('/getgoalkpis', methods=['GET'])
@login_required
def getGoalKPIs():
    
    data_obj_list = GoalGoalKPI.query.all()
    print(data_obj_list)
    data = []
    
    for item_obj in data_obj_list:
        # print (item_obj)
        dict={}
        dict["id"] = item_obj.id
        dict["goal"] = item_obj.goal_name
        dict["goalkpis"] = item_obj.goalKPI_list
    
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
 
    