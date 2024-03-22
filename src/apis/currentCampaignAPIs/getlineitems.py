from flask import Blueprint, jsonify, session, request
import logging
from flask_login import login_required
from models import LineItems, LineItemMetrics
from settings.functions import *
from decimal import Decimal
from sqlalchemy.orm import joinedload
from util.decorators import cache_route

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

lineitems_blueprint = Blueprint('lineitems', __name__)

@lineitems_blueprint.route('/getlineitems', methods=['POST'])
@login_required
# @cache_route(seconds = 2 * 60 * 60)
def getLineItems():
    request_data = request.json
    campaign_order_id = request_data["campaign"]["order_id"]

    # Use a joined load to fetch LineItemMetrics along with LineItems
    line_items_objs = LineItems.query.filter_by(order_id=campaign_order_id).options(joinedload(LineItems.line_item_metric)).all()


    # select * from lineitems join LineItemMetrics where orderid = camp_oder_id

    data = []

    for item_obj in line_items_objs:
        line_item_metrics = item_obj.line_item_metric

        # Calculate metrics
        dict = {
            "total_line_items": 0,
            "total_cost": round(sum(metric.totalCost for metric in line_item_metrics), 3),
            "total_sales": round(sum(metric.totalSales14d for metric in line_item_metrics), 3),
            "total_snss": sum(metric.totalSubscribeAndSaveSubscriptions14d for metric in line_item_metrics),
            "dpv": round(sum(metric.dpv14d for metric in line_item_metrics), 3),
            "ntb_purchases": sum(metric.newToBrandPurchases14d for metric in line_item_metrics),
            "impressions": sum(metric.impressions for metric in line_item_metrics),
            "clickthroughs": sum(metric.clickThroughs for metric in line_item_metrics),
            "atc": sum(metric.atc14d for metric in line_item_metrics),
            "total_atc": sum(metric.totalAddToCart14d for metric in line_item_metrics),
            "brand_search": sum(metric.brandSearch14d for metric in line_item_metrics),
            "brand_search_rate": round(sum(metric.brandSearchRate14d for metric in line_item_metrics), 5),
            "total_units_sold": sum(metric.totalUnitsSold14d for metric in line_item_metrics),
            "total_purchases": sum(metric.totalPurchases14d for metric in line_item_metrics),
            "purchases": sum(metric.purchases14d for metric in line_item_metrics),
            "units_sold": sum(metric.unitsSold14d for metric in line_item_metrics),
            "product_sales": round(sum(metric.sales14d for metric in line_item_metrics), 3),
            "ecpp": round(sum(metric.totalCost for metric in line_item_metrics) / sum(metric.impressions for metric in line_item_metrics), 5) if sum(metric.impressions for metric in line_item_metrics) != 0 else 0,
            "total_dpv": sum(metric.totalDetailPageViews14d for metric in line_item_metrics),
            "gross_impressions": sum(metric.grossImpressions for metric in line_item_metrics),
            "subscription": sum(metric.subscribe14d for metric in line_item_metrics),
            "total_ntb_purchases": sum(metric.totalNewToBrandPurchases14d for metric in line_item_metrics),
            "total_ntb_product_sales": round(sum(metric.totalNewToBrandProductSales14d for metric in line_item_metrics),3),
            "ntb_sales": round(sum(metric.newToBrandProductSales14d for metric in line_item_metrics),3),
            "measurable_impressions": sum(metric.measurableImpressions for metric in line_item_metrics),
            "viewable_impressions": sum(metric.viewableImpressions for metric in line_item_metrics)
        }
        # dict["dpv"] = float(dict["dpv"])
        dict["line_item_id"] = item_obj.line_item_id
        dict["line_item_name"] = item_obj.line_item_name
        dict["start_time"] = item_obj.start_time
        dict["end_time"] = item_obj.end_time
        dict["line_item_type"] = item_obj.line_item_type
        dict["bid"] = item_obj.bidding["baseSupplyBid"]

        # Calculate additional metrics
        dict["percent_of_purchases_ntb"] = round(percent_of_purchases_NTB(dict["ntb_purchases"], dict["total_purchases"]), 5) if dict["total_purchases"] != 0 else 0
        dict["percent_of_purchases_total_ntb"] = round(percent_of_purchases_total_NTB(dict["total_ntb_purchases"], dict["total_purchases"]), 5) if dict["total_purchases"] != 0 else 0
        dict["dpvr"] = round(dpvr(dict["total_dpv"], dict["impressions"]), 5) if dict["impressions"] != 0 else 0
        dict["cvr_clickthroughs"] = round(cvr_clickthroughs(dict["clickthroughs"], dict["purchases"]), 5) if dict["purchases"] != 0 else 0
        dict["ecpm"] = round(ecpm(dict["total_cost"], dict["impressions"]), 5) if dict["impressions"] != 0 else 0
        dict["ntb_roas"] = round(ntb_roas(dict["ntb_sales"], dict["total_cost"]), 5) if dict["total_cost"] != 0 else 0
        dict["total_ntb_roas"] = round(total_ntb_roas(dict["total_ntb_product_sales"], dict["total_cost"]), 5) if dict["total_cost"] != 0 else 0
        dict["ctr"] = round(ctr(dict["clickthroughs"], dict["impressions"]), 5) if dict["impressions"] != 0 else 0
        dict["snssr"] = round(snssr(dict["total_snss"], dict["impressions"]), 5) if dict["impressions"] != 0 else 0
        dict["roas"] = round(roas(dict["product_sales"], dict["total_cost"]), 5) if dict["total_cost"] != 0 else 0
        dict["total_roas"] = round(total_roas(dict["total_sales"], dict["total_cost"]), 5) if dict["total_cost"] != 0 else 0
        dict["ecpc"] = round(ecpc(dict["total_cost"], dict["clickthroughs"]), 5) if dict["clickthroughs"] != 0 else 0
        dict["purchase_rate"] = round(purchase_rate(dict["purchases"], dict["gross_impressions"]), 5) if dict["gross_impressions"] != 0 else 0
        dict["ppd"] = round(ppd(dict["purchases"], dict["total_cost"]), 5) if dict["total_cost"] != 0 else 0
        dict["cpp"] = round(cpp(dict["total_cost"], dict["purchases"]), 5) if dict["purchases"] != 0 else 0
        dict["brand_search_rate"] = round(brand_search_rate(dict["brand_search"], dict["impressions"]), 5) if dict["impressions"] != 0 else 0
        dict["viewability_rate"] = round(viewability_rate(dict["viewable_impressions"], dict["measurable_impressions"]), 5) if dict["measurable_impressions"] != 0 else 0

        
        data.append(dict)

    response = {
        "data": data,
        "status": {
            "statusMessage": "Success",
            "statusCode": 200
        }
    }

    return jsonify(response)

