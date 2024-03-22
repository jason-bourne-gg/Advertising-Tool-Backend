from flask import Blueprint, jsonify, session, request, make_response
import datetime
import logging
from flask_login import login_required
from models import Campaign, LineItemMetrics, LineItems
from database import db
from datetime import datetime
from settings.functions import *
from sqlalchemy import and_, func, distinct
from collections import defaultdict
from datetime import datetime, timedelta
from apis.currentCampaignAPIs.overallPerformance import getAggregatedMetrics, getDerivedMetrics
from util.decorators import cache, update_user_activity


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

campaignscorecard_blueprint = Blueprint('campaignscorecard', __name__)

brand_store = {}


@campaignscorecard_blueprint.route('/getcampaignscorecard', methods=['POST'])
@login_required
@update_user_activity
def campaignScorecard():
    try: 
        request_data =request.json
        startDate = datetime.strptime(request_data["start_date"], "%Y-%m-%d")
        endDate = datetime.strptime(request_data["end_date"], "%Y-%m-%d")
        order_id = request_data["order_id"]

        metrics_query = getAggregatedMetrics([order_id], startDate, endDate)
        derived_metrics = getDerivedMetrics(metrics_query)

        # Combine aggregated and derived metrics into a single dictionary
        result_dict = {**metrics_query._asdict(), **derived_metrics}

        response = {
                "data": [result_dict],
                "status": {
                    "statusMessage": "Success",
                    "statusCode": 200
                }
            }
        # print(response)    
        return response

    except Exception as e:    
        error_message = str(e)  
        error_response = {
            "status": {
                "statusMessage": "Error",
                "statusCode": 500
            },
            "error_message": error_message
        }
        return jsonify(error_response), 500
































def get_week_start(date):
    '''
    Week starts from Sunday
    '''
    weekday = date.weekday()
    start_date = date - timedelta(days=weekday + 1)

    # If the given date is Sunday, return it as the start date
    if weekday == 6:
        start_date = date
    return start_date  


def aggregate_data(data, interval):
    aggregated_data = {}

    for date_str, value in data.items():
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        if interval == 'daily':
            interval_key = date_str

        elif interval == 'weekly':
            week_start = get_week_start(date)
            # interval_key = f'{week_start.strftime("%Y-%m-%d")} - {(week_start + timedelta(days=6)).strftime("%Y-%m-%d")}'
            interval_key = f'{week_start.strftime("%Y-%m-%d")}'

        elif interval == 'monthly':
            interval_key = date.replace(day=1).strftime('%Y-%m')

        else:
            raise ValueError("Invalid interval. Please choose 'weekly','monthly' or 'daily'.")

        if interval_key not in aggregated_data:
            aggregated_data[interval_key] = {'value': 0}

        aggregated_data[interval_key]['value'] += value
        # print("aggregated_data = ",aggregated_data)

    return aggregated_data


def aggregate_data_for_functionMetric(data, interval, col1, col2):
    aggregated_data = {}

    for date_str, values in data.items():
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        if interval == 'daily':
            interval_str = date_str

        elif interval == 'weekly':
            interval_start = get_week_start(date)
            interval_end = interval_start + timedelta(days=6)
            # interval_str = f'{interval_start.strftime("%Y-%m-%d")} - {interval_end.strftime("%Y-%m-%d")}'
            interval_str = f'{interval_start.strftime("%Y-%m-%d")}'
        elif interval == 'monthly':
            interval_start = date.replace(day=1)
            interval_str = interval_start.strftime('%Y-%m')
        else:
            raise ValueError("Invalid interval. Please choose 'daily', 'weekly' or 'monthly'.")

        if interval_str not in aggregated_data:
            aggregated_data[interval_str] = {col1: 0, col2: 0}

        aggregated_data[interval_str][col1] += values[col1]
        aggregated_data[interval_str][col2] += values[col2]

    return aggregated_data


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

function_metrics = ['dpvr', 'percent_of_purchases_ntb', 'percent_of_purchases_total_ntb', 'cvr_clickthroughs', 'ecpm', 'ntb_roas', 'total_ntb_roas', 'ctr', 'snssr', 'roas', 'total_roas', 'ecpc', 'purchase_rate', 'ppd', 'cpp', 'brand_search_rate', 'viewability_rate']

@campaignscorecard_blueprint.route('/getcampaignscorecardgraph', methods=['POST'])
@login_required
@update_user_activity
def campaign_scorecard_graph():
    request_data = request.json
    start_date = datetime.strptime(request_data["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(request_data["end_date"], "%Y-%m-%d")
    interval = request_data["interval"]

    # Calculate daily date intervals
    current_date = start_date
    date_interval = []
    while current_date <= end_date:
        date_interval.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)


    if request_data["metric"] in function_metrics:
        col1, col2 = metricsMapping2(request_data["metric"])
        if col1 is None or col2 is None:
            return jsonify({"error": "Error in fetching mapping column, please check the column value passed in the request"}), 400

        dated_metric_objs = LineItemMetrics.query \
            .with_entities(getattr(LineItemMetrics, col1), getattr(LineItemMetrics, col2), LineItemMetrics.date) \
            .filter(and_(LineItemMetrics.order_id == request_data["order_id"],
                         LineItemMetrics.date.in_(date_interval))) \
            .all()

        accumulated_data = defaultdict(lambda: {col1: 0, col2: 0})

        for row in dated_metric_objs:
            date = row[2].strftime('%Y-%m-%d')
            value1 = row[0]
            value2 = row[1]

            accumulated_data[date][col1] += value1
            accumulated_data[date][col2] += value2

        if interval == 'weekly' or interval == 'monthly':
            aggregated_result = aggregate_data_for_functionMetric(accumulated_data, interval, col1, col2)
        else:
            aggregated_result = aggregate_data_for_functionMetric(accumulated_data, 'daily', col1, col2)

        data = []
        for date_range, values in sorted(aggregated_result.items()):
            funct_output = function_mapping[request_data["metric"]](values[col1], values[col2])
            temp_data = {"date": date_range, "value": funct_output}
            data.append(temp_data)

        response = {
            "data": {"sigmoidControl": data},
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }
    else:
        try:
            metric_column = metricsMapping(request_data["metric"]).strip('"')
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        dated_metric_objs = LineItemMetrics.query \
            .with_entities(getattr(LineItemMetrics, metric_column), LineItemMetrics.date) \
            .filter(and_(LineItemMetrics.order_id == request_data["order_id"],
                         LineItemMetrics.date.in_(date_interval))) \
            .all()

        data_accumulated = defaultdict(float)

        for row in dated_metric_objs:
            date = row[1].strftime('%Y-%m-%d')
            value = row[0]
            data_accumulated[date] += float(value)

        if interval == 'weekly' or interval == 'monthly':
            aggregated_result = aggregate_data(data_accumulated, interval)
        else:
            aggregated_result = aggregate_data(data_accumulated, 'daily')

        data = [{"date": date_range, "value": values['value']} for date_range, values in sorted(aggregated_result.items())]

        response = {
            "data": {"sigmoidControl": data},
            "status": {
                "statusMessage": "Success",
                "statusCode": 200
            }
        }

    return response
