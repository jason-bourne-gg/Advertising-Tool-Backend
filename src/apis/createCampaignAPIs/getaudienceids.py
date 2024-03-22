from flask import Blueprint, jsonify,session, request
import logging
from flask_login import login_required 
from models import AudienceId
from sqlalchemy import and_



# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

audienceids_blueprint = Blueprint('audienceids', __name__)

audienceids_store = {}

@audienceids_blueprint.route('/getaudienceids', methods=['GET', 'POST'])
@login_required
def getAudienceIds():
    request_data = request.json
    # print(request_data)
    searchstring = request_data["searchString"]
    # print(searchstring)
    data = []

    if searchstring == "":
        data_obj_list = AudienceId.query.all()
        # print(data_obj_list)
        for audienceids_obj in data_obj_list :
            # print(audienceids_obj.id, audienceids_obj.audience_id, audienceids_obj.audience_name)
            dict={}
            dict["audience_id"] = audienceids_obj.audienceId
            dict["audience_name"] = audienceids_obj.audienceName
            # print(dict)
            data.append(dict)
            # print(data)

    else:
        data_obj_list = AudienceId.query.filter(and_(AudienceId.audienceName.ilike(f"%{searchstring}%"), AudienceId.status == "Active", AudienceId.category != 'Third-party')).all()
        # print(data_obj_list)
        for audienceids_obj in data_obj_list :
            # print(audienceids_obj.id, audienceids_obj.audience_id, audienceids_obj.audience_name)
            dict={}
            dict["audience_id"] = audienceids_obj.audienceId
            dict["audience_name"] = audienceids_obj.audienceName

            if audienceids_obj.category == "Negative Targeting" :
                dict["include"] = False
                dict["disabled"] = True
            else :
                dict ['include'] = True
                dict["disabled"] = False

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
 
    