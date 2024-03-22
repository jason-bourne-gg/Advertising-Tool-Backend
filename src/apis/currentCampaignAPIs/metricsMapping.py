from flask import Blueprint, jsonify,session,request,make_response
import datetime
import logging
from flask_login import login_required 
import requests
import json
from models import MetricsMapping
from database import db
from datetime import datetime
from settings.functions import *

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

metricsmapping_blueprint = Blueprint('metricsmapping', __name__)

brand_store = {}

@metricsmapping_blueprint.route('/getmetricsmapping', methods=['GET'])
@login_required
def metricsMapping():    

    metricmap_objs = MetricsMapping.query.all()
    data= []
    for metricmap_obj in metricmap_objs:
        dict = {}
        dict["column_name"] = metricmap_obj.metric_column_name
        dict["label"] = metricmap_obj.metric_column_label
        data.append(dict)


    response = {
        "data": data,
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
    }
        
    return response    