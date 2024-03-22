from flask import Blueprint, jsonify,session,request,make_response
import datetime
import logging
from flask_login import login_required 
from models import Campaign,LineItemMetrics,LineItems
from database import db
from datetime import datetime
from settings.functions import *
from sqlalchemy import and_,func,distinct
from sqlalchemy.orm import aliased
from datetime import datetime, timedelta
from collections import defaultdict
from apis.currentCampaignAPIs.campaignScorecard import aggregate_data_for_functionMetric,aggregate_data
from util.decorators import cache, update_user_activity

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

overallperformance_blueprint = Blueprint('overallperformance', __name__)

brand_store = {}



@overallperformance_blueprint.route('/getoverallperformance', methods=['POST'])
@login_required
@update_user_activity
def overallPerformance():   

    if request.method == "POST":
        request_data = request.json
        startDate = datetime.strptime(request_data["start_date"], "%Y-%m-%d")
        endDate = datetime.strptime(request_data["end_date"], "%Y-%m-%d")

        brand_obj_list = request_data["brand"]
        brand_ids = set(brand_obj['id'] for brand_obj in brand_obj_list)
        camp_obj_list = Campaign.query.filter(
            Campaign.brand_id.in_(brand_ids),
            Campaign.campaign_status == "RUNNING"
        ).all()
        dict = {}
        order_id_dict ={}
        for camp_obj in camp_obj_list:
            order_id_dict[camp_obj.order_id] = None  # Using a dictionary to avoid duplicates

        # Get the order IDs as a list
        order_ids_array = list(order_id_dict.keys())     
    
        metrics_query = getAggregatedMetrics(order_ids_array, startDate, endDate)
        derived_metrics = getDerivedMetrics(metrics_query)

        # Combine aggregated and derived metrics into a single dictionary
        dict = {**metrics_query._asdict(), **derived_metrics}
        dict["total_campaigns_running"] = len(camp_obj_list)

        response = {
                "data": [dict],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }
        # print(response)    
        return response














@overallperformance_blueprint.route('/getoverallperformancegraph', methods=['POST'])
@login_required
@update_user_activity
def overallPerformanceGraph():
    request_data =request.json
    # print(request_data)
    startDate = datetime.strptime(request_data["start_date"], "%Y-%m-%d")
    endDate = datetime.strptime(request_data["end_date"], "%Y-%m-%d")
    interval = request_data["interval"]

    # Calculate daily date intervals
    current_date = startDate
    dateInterval = []
    while current_date <= endDate:
        dateInterval.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    # print(dateInterval)

    function_mapping = {
        "percent_of_purchases_ntb": percent_of_purchases_NTB,
        "ecpm": ecpm,
        "ntb_roas": ntb_roas,
        "total_ntb_roas" :total_ntb_roas,
        "ctr":ctr,
        "snssr":snssr,
        "roas":roas,
        "total_roas":total_roas,    
        "ecpc":ecpc,
        "purchase_rate":purchase_rate,
        "ppd":ppd,
        "cpp":cpp,
        "dpvr":dpvr,
        "percent_of_purchases_total_ntb":percent_of_purchases_total_NTB,
        "cvr_clickthroughs":cvr_clickthroughs,
        "brand_search_rate":brand_search_rate,
        "viewability_rate":viewability_rate  
    }

    brand_obj_list = request_data["brand"]
    brand_ids = [brand_obj["id"] for brand_obj in brand_obj_list]
    camp_obj_list = Campaign.query.filter(Campaign.brand_id.in_(brand_ids), Campaign.campaign_status == "RUNNING").all()    

    functionMetrics = ['dpvr', 'percent_of_purchases_ntb', 'percent_of_purchases_total_ntb', 'cvr_clickthroughs', 'ecpm', 'ntb_roas', 'total_ntb_roas', 'ctr', 'snssr', 'roas', 'total_roas', 'ecpc', 'purchase_rate', 'ppd', 'cpp', 'brand_search_rate','viewability_rate']
    
    if request_data["metric"] in functionMetrics:
        col1, col2 = metricsMapping2(request_data["metric"])
        # print (col1,col2)
        if col1 is None or col2 is None:
            return ("error in fetching mapping column, please check column value passed in request")


        dated_metric_objs_sigmoid = LineItemMetrics.query \
        .with_entities(getattr(LineItemMetrics, col1), getattr(LineItemMetrics, col2), LineItemMetrics.date) \
        .filter(and_(LineItemMetrics.order_id.in_([campaign_obj.order_id for campaign_obj in camp_obj_list]), \
                    LineItemMetrics.date.in_(dateInterval))) \
        .all()


        accumulated_data_1 = {}  # Dictionary to store accumulated values for each date for sigmoid conrot

        for row in dated_metric_objs_sigmoid:
            # print(row)
            date = row[2].strftime('%Y-%m-%d')
            value1 = row[0]
            value2 = row[1]

            if date in accumulated_data_1:
                accumulated_data_1[date][col1] += value1
                accumulated_data_1[date][col2] += value2
            else:
                accumulated_data_1[date] = {col1: value1, col2: value2}

        print("interval = ",interval)
        print("accumulated_data = ", accumulated_data_1)
        if interval == 'weekly' or interval == 'monthly':
            aggregated_result = aggregate_data_for_functionMetric(accumulated_data_1, interval, col1, col2)
            print("aggregated_result =", aggregated_result)

            data =[]
            for date_range, values in sorted(aggregated_result.items()):
                funct_output = function_mapping[request_data["metric"]](values[col1],values[col2])
                temp_data = {"date" : date_range , "value" : funct_output}
                data.append(temp_data)

            response = {
                "data": [{"sigmoidControl" : data, "reckittConrol" : []}],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }    


        else:
            response = {
                "data": [{"sigmoidControl" : [{'date': date, 'value': function_mapping[request_data["metric"]](accumulated_data_1[date][col1],accumulated_data_1[date][col2])} for date, value in sorted(accumulated_data_1.items())],
                         "reckittConrol" : [],
                         }],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }
            
        return response
    


        sorted_data = {
            "sigmoidControl": [
                {
                    "date": date,
                    "value": function_mapping[request_data["metric"]](
                        accumulated_data_1[date][col1], accumulated_data_1[date][col2]
                    ),
                }
                for date in sorted(accumulated_data_1.keys())
            ],
            "reckittControl": [
                {
                    "date": date,
                    "value": function_mapping[request_data["metric"]](
                        accumulated_data_2[date][col1], accumulated_data_2[date][col2]
                    ),
                }
                for date in sorted(accumulated_data_2.keys())
            ],
        }



        response = {
                "data":[sorted_data],
                # "data" : [data_accumulated],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }
            
        return response
    

    else:
        try:
            metric_column = metricsMapping(request_data["metric"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        metric_column = metric_column.strip('"')
        # print(metric_column)

        dated_metric_objs_sigmoid = LineItemMetrics.query \
        .with_entities(getattr(LineItemMetrics, metric_column), LineItemMetrics.date) \
        .filter(and_(LineItemMetrics.order_id.in_([campaign_obj.order_id for campaign_obj in camp_obj_list]), \
                    LineItemMetrics.date.in_(dateInterval))) \
        .all()

        # print(dated_metric_objs)

        # cannot use normal dict becasue we will have to define every key beforehand, as we did in scorecard api
        # Create a defaultdict to store the accumulated data for each date,
        # default dict produces a new value if key is not present
        data_accumulated_1 = defaultdict(float)
        
        # Accumulate the data for each date
        for row in dated_metric_objs_sigmoid:
            # print(row)
            date = row[1].strftime('%Y-%m-%d')
            value = row[0]
            data_accumulated_1[date] += float(value)

        print("data_accumulated = ", data_accumulated_1)        
        if interval == 'weekly' or interval == 'monthly':
            aggregated_result = aggregate_data(data_accumulated_1, interval)
            print("aggregated_result =", aggregated_result)

            data =[]
            for date_range, values in sorted(aggregated_result.items()):
                temp_data = {"date" : date_range, "value" : values['value']}
                data.append(temp_data)

            response = {
                "data": [{"sigmoidControl" : data, 
                         "reckittControl" : []}],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }    

       

        else:
            
            response = {
                "data": [{"sigmoidControl" : [], "reckittControl" : []}],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }
            for date, value in sorted(data_accumulated_1.items()):
                response["data"][0]["sigmoidControl"].append({
                "date": date,
                "value": value
            })
            
        return response
    



    
        sorted_data = {
            "sigmoidControl": [
                {"date": date, "value": value}
                for date, value in sorted(data_accumulated_1.items())
            ],
            "reckittControl": [
                {"date": date, "value": value}
                for date, value in sorted(data_accumulated_2.items())
            ],
        }


        response = {
                "data": [sorted_data],
                # "data" : [data_accumulated],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }
            
        return response
    





'''
        dated_metric_objs_sigmoid = LineItemMetrics.query \
        .with_entities(getattr(LineItemMetrics, col1), getattr(LineItemMetrics, col2), LineItemMetrics.date) \
        .filter(and_(LineItemMetrics.order_id.in_([campaign_obj.order_id for campaign_obj in camp_obj_list]), \
                    LineItemMetrics.date.in_(dateInterval), 
                    LineItemMetrics.line_item_name.like('%Reckitt%'))) \
        .all()

        accumulated_data_2 = {}  # Dictionary to store accumulated values for each date

        for row in dated_metric_objs_sigmoid:
            # print(row)
            date = row[2].strftime('%Y-%m-%d')
            value1 = row[0]
            value2 = row[1]

            if date in accumulated_data_2:
                accumulated_data_2[date][col1] += value1
                accumulated_data_2[date][col2] += value2
            else:
                accumulated_data_2[date] = {col1: value1, col2: value2}
'''





'''
# getting data with reckitt control 
        dated_metric_objs_reckitt = LineItemMetrics.query \
        .with_entities(getattr(LineItemMetrics, metric_column), LineItemMetrics.date) \
        .filter(and_(LineItemMetrics.order_id.in_([campaign_obj.order_id for campaign_obj in camp_obj_list]), \
                    LineItemMetrics.date.in_(dateInterval),
                    LineItemMetrics.line_item_name.like('%Reckitt%'))) \
        .all()
        # print(dated_metric_objs)
        data_accumulated_2 = defaultdict(float)
        
        # Accumulate the data for each date
        for row in dated_metric_objs_reckitt:
            # print(row)
            date = row[1].strftime('%Y-%m-%d')
            value = row[0]
            data_accumulated_2[date] += float(value)

        # print("Accumulated data:")
        # print(data_accumulated_1)

'''