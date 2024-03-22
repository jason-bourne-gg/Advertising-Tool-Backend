from flask import Blueprint, jsonify,session,request
import logging
from flask_login import login_required 
from models import Brand,Region,CampaignType,TargetPlatform,user_brand,UserDetails, user_region, user_campaign_type, user_target_platform
from database import db
import requests
from sqlalchemy import text
from sqlalchemy.orm import joinedload


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

usersettings_blueprint = Blueprint('usersettings', __name__)

usersettings_store = {}

@usersettings_blueprint.route('/getuserpermissions', methods=['POST'])
@login_required
def getUserPermissions():
    request_data = request.json
    session_user_email  = request_data['email']
    session_user__id = request_data ['id']

    '''
    SELECT brand.* --select all cols of brand ....if just * then combo of cols from brand and user_brand
    FROM brand
    JOIN user_brand ON brand.id = user_brand.brand_id
    WHERE user_brand.user_id = 1;
    '''

    brand_objs = db.session.query(Brand).join(
    user_brand, user_brand.c.brand_id == Brand.id
    ).filter(user_brand.c.user_id == session_user__id).all()
    # print(brand_objs)
    accessible_brands =[]
    for brand_obj in brand_objs :
        # print(brand_obj.id, brand_obj.brand_code, brand_obj.brand_name)
        dict={}
        dict["id"]=brand_obj.id
        dict["code"]=brand_obj.brand_code
        dict["name"]=brand_obj.brand_name
        accessible_brands.append(dict)


    region_objs = db.session.query(Region).join(
    user_region, user_region.c.region_id == Region.id
    ).filter(user_region.c.user_id == session_user__id).all()
    # print(region_objs)
    accessible_regions = []
    for region_obj in region_objs :
        dict={}
        dict["id"]=region_obj.id
        dict["code"]=region_obj.region_code
        dict["name"]=region_obj.region_name
        accessible_regions.append(dict)


    target_platform__objs = db.session.query(TargetPlatform).join(
        user_target_platform, user_target_platform.c.target_platform_id == TargetPlatform.id
    ).filter(user_target_platform.c.user_id == session_user__id).all()

    accessibe_platforms = []  
    for target_platform__obj in target_platform__objs:
        platform_dict = {}
        platform_dict["id"] = target_platform__obj.id
        platform_dict["name"] = target_platform__obj.platform

        campaign_type_objs = db.session.query(CampaignType).join(
            user_campaign_type, user_campaign_type.c.campaign_type_id == CampaignType.id
        ).filter(
            user_campaign_type.c.user_id == session_user__id,
            CampaignType.target_platform_id == target_platform__obj.id
        ).all()

        accessible_campaign_types = []
        for campaign_type_obj in campaign_type_objs:
            campaign_type_dict = {}
            campaign_type_dict["id"] = campaign_type_obj.id
            campaign_type_dict["name"] = campaign_type_obj.campaign_type
            accessible_campaign_types.append(campaign_type_dict)

        platform_dict["campaign_types"] = accessible_campaign_types
        accessibe_platforms.append(platform_dict)
            

    response = {
        "data": {"accessible_regions":accessible_regions, "accessible_brands":accessible_brands , "accessibe_platforms": accessibe_platforms},
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
    }

    return response



@usersettings_blueprint.route('/setuserpermissions', methods=['POST', 'PUT'])
# @login_required
def setUserPermissions():
    # try:
        payload = request.json
        user_email = payload['user_details']['email']
        user_id = payload['user_details']['id']
        userRole = payload ['user_details']['role']

        # user_obj = UserDetails.query.filter(email = user_email).first()
        user_obj = UserDetails.query.filter_by(email=user_email).first()

        if user_obj:
            user_obj.role = userRole
            db.session.commit()
            print(f"Role for user with email {user_email} updated to {userRole}.")
        else:
            print(f"User with email {user_email} not found.")

        print (user_email, user_id)

        # Accessible regions
        accessible_regions = payload['data']['accessible_regions']
        
        # Create the delete statement with the WHERE condition
        delete_query = text (f"DELETE FROM user_region WHERE user_id = {user_id};")
        db.session.execute(delete_query)
        print(f"deleted all regions accesses for user with email {user_email}")

        for region in accessible_regions:
            statement = user_region.insert().values(user_id=user_id, region_id=region['id'])
            db.session.execute(statement)
            db.session.commit()
            print(f"New region: {region} added for user with email = {user_email}")

            
        # delete any brand accesses for given user
        delete_query = text (f"DELETE FROM user_brand WHERE user_id = {user_id};")
        db.session.execute(delete_query)
        print(f"deleted all brand accesses for user with email {user_email}")

        # Accessible brands
        accessible_brands = payload['data']['accessible_brands']
        for brand in accessible_brands:
            statement = user_brand.insert().values(user_id=user_id, brand_id=brand['id'])
            db.session.execute(statement)
            db.session.commit()
            print(f"New brand : {brand} added for user with email = {user_email}")
            
  
        # Accessible campaign types and platforms
        # first delete all the access for campaigntypes and platforms
        delete_query = text (f"DELETE FROM user_campaign_type WHERE user_id = {user_id};")
        db.session.execute(delete_query)
        print(f"deleted all campaigntype accesses for user with email {user_email}")

        delete_query = text (f"DELETE FROM user_target_platform WHERE user_id = {user_id};")
        db.session.execute(delete_query)
        print(f"deleted all platform accesses for user with email {user_email}")

        accessible_platforms = payload['data']['accessible_platforms']
        for platform in accessible_platforms:
            for campaign_type in platform['campaign_types']:
                statement = user_campaign_type.insert().values(user_id=user_id, campaign_type_id=campaign_type['id'])
                db.session.execute(statement)
                db.session.commit()
                print(f"New campaign_type: {campaign_type} added for user with email = {user_email}")
                

            statement = user_target_platform.insert().values(user_id=user_id, target_platform_id=platform['id'])
            db.session.execute(statement)
            db.session.commit()
            print(f"New target_platform: {platform} added for user with email = {user_email}")

        db.session.commit()

        response = {
        "message": {"message": "User access updated successfully."},
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
        }
        return response


    # except Exception as e:
    #     return jsonify({"error": str(e)}), 500