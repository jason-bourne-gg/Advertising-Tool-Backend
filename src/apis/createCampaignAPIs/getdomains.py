from flask import Blueprint, jsonify,session, request
import logging
from flask_login import login_required 
from models import DomainNames



# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

domainnames_blueprint = Blueprint('domainnames', __name__)

domainnames_store = {}

@domainnames_blueprint.route('/getdomainnames', methods=['GET', 'POST'])
@login_required
def getDomainNames():
    request_data = request.json
    # print(request_data)
    searchstring = request_data["searchString"]
    # print(searchstring)
    data = []

    if searchstring == "":
        data_obj_list = DomainNames.query.all()
        print(data_obj_list)
        for domainnames_obj in data_obj_list :
            # print(domainnames_obj.id, domainnames_obj.domain_id, domainnames_obj.domain_name)
            dict={}
            dict["domain_id"] = domainnames_obj.domain_id
            dict["domain_name"] = domainnames_obj.domain_name
            # print(dict)
            data.append(dict)
            # print(data)


    else:     
        data_obj_list = DomainNames.query.filter(DomainNames.domain_name.ilike(f"%{searchstring}%")).all()
        # print(data_obj_list)
        for domainnames_obj in data_obj_list :
            # print(domainnames_obj.id, domainnames_obj.domain_id, domainnames_obj.domain_name)
            dict={}
            dict["domain_id"] = domainnames_obj.domain_id
            dict["domain_name"] = domainnames_obj.domain_name
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
 
    