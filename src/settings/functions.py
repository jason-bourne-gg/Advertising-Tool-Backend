from models import Campaign,LineItemMetrics,LineItems
from database import db
from sqlalchemy import and_,func,distinct


# Helper function to calculate aggregated metrics
def getAggregatedMetrics(orderId_array, start_date, end_date):
    metrics_query = db.session.query(
        func.count(distinct(LineItemMetrics.line_item_id)).label('total_line_items'),
        func.sum(LineItemMetrics.totalCost).label('total_cost'),
        func.sum(LineItemMetrics.impressions).label('impressions'),
        func.sum(LineItemMetrics.clickThroughs).label('clickthroughs'),
        func.sum(LineItemMetrics.atc14d).label('atc'),
        func.sum(LineItemMetrics.totalAddToCart14d).label('total_atc'),
        func.sum(LineItemMetrics.totalSubscribeAndSaveSubscriptions14d).label('total_snss'),
        func.sum(LineItemMetrics.newToBrandPurchases14d).label('ntb_purchases'),
        func.sum(LineItemMetrics.newToBrandProductSales14d).label('ntb_sales'),
        func.sum(LineItemMetrics.totalNewToBrandPurchases14d).label('total_ntb_purchases'),
        func.sum(LineItemMetrics.totalNewToBrandProductSales14d).label('total_ntb_product_sales'),
        func.sum(LineItemMetrics.subscribe14d).label('subscription'),
        func.sum(LineItemMetrics.sales14d).label('product_sales'),
        func.sum(LineItemMetrics.totalSales14d).label('total_sales'),
        func.sum(LineItemMetrics.brandSearch14d).label('brand_search'),
        func.sum(LineItemMetrics.unitsSold14d).label('units_sold'),
        func.sum(LineItemMetrics.totalUnitsSold14d).label('total_units_sold'),
        func.sum(LineItemMetrics.purchases14d).label('purchases'),
        func.sum(LineItemMetrics.totalPurchases14d).label('total_purchases'),
        func.cast(func.sum(LineItemMetrics.dpv14d), db.Float).label('dpv'),
        func.sum(LineItemMetrics.totalDetailPageViews14d).label('total_dpv'),
        func.sum(LineItemMetrics.grossImpressions).label('gross_impressions'),
        func.sum(LineItemMetrics.measurableImpressions).label('measurable_impressions'),
        func.sum(LineItemMetrics.viewableImpressions).label('viewable_impressions')
        # Add other aggregated metrics here
    ). filter(and_( LineItemMetrics.order_id.in_(orderId_array),
                    LineItemMetrics.date >= start_date, LineItemMetrics.date <= end_date)
    ).first()  # Fetch the first result row

    return metrics_query


def getDerivedMetrics (metrics_query):
    # Add derived Metrics below
    percent_of_purchases_ntb = (
        round((metrics_query.ntb_purchases * 100) / metrics_query.total_purchases, 4)
        if metrics_query.total_purchases != 0
        else 0
    )
    
    ecpm = (
        round((metrics_query.total_cost * 1000) / metrics_query.impressions, 4)
        if metrics_query.impressions != 0
        else 0
    )
    
    ntb_rev = metrics_query.ntb_sales
    ntb_roas = (
        round(ntb_rev / metrics_query.total_cost, 4)
        if metrics_query.total_cost != 0
        else 0
    )

    total_ntb_rev = metrics_query.total_ntb_product_sales
    total_ntb_roas = (
        round(total_ntb_rev / metrics_query.total_cost, 4)
        if metrics_query.total_cost != 0
        else 0
    )

    ctr = (
        round((metrics_query.clickthroughs * 100) / metrics_query.impressions, 4)
        if metrics_query.impressions != 0
        else 0
    )

    snssr = (
        round(metrics_query.total_snss / metrics_query.impressions, 4)
        if metrics_query.impressions != 0
        else 0
    )

    roas = (
        round(metrics_query.product_sales / metrics_query.total_cost, 4)
        if metrics_query.total_cost != 0
        else 0
    )

    total_roas = (
        round(metrics_query.total_sales / metrics_query.total_cost, 4)
        if metrics_query.total_cost != 0
        else 0
    )

    ecpc = (
        round(metrics_query.total_cost / metrics_query.clickthroughs, 4)
        if metrics_query.clickthroughs != 0
        else 0
    )

    purchase_rate = (
        round((metrics_query.purchases * 100) / metrics_query.impressions, 4)
        if metrics_query.impressions != 0
        else 0
    )

    ppd = (
        round(metrics_query.purchases / metrics_query.total_cost, 4)
        if metrics_query.total_cost != 0
        else 0
    )

    cpp = (
        round(metrics_query.total_cost / metrics_query.purchases, 4)
        if metrics_query.purchases != 0
        else 0
    )

    dpvr = (
        round((metrics_query.total_dpv * 100) / metrics_query.impressions, 4)
        if metrics_query.impressions != 0
        else 0
    )

    percent_of_purchases_total_ntb = (
        round((metrics_query.total_ntb_purchases * 100) / metrics_query.total_purchases, 4)
        if metrics_query.total_purchases != 0
        else 0
    )

    cvr_clickthroughs = (
        round((metrics_query.clickthroughs * 100) / metrics_query.purchases, 4)
        if metrics_query.purchases != 0
        else 0
    )

    brand_search_rate = (
        round((metrics_query.brand_search * 100) / metrics_query.impressions, 4)
        if metrics_query.impressions != 0
        else 0
    )

    viewability_rate = (
        round((metrics_query.viewable_impressions * 100) / metrics_query.measurable_impressions, 4)
        if metrics_query.measurable_impressions != 0
        else 0
    )

    return {
        # Dervied Metrics
        "percent_of_purchases_ntb": percent_of_purchases_ntb,
        "ecpm": ecpm,
        "ntb_roas": ntb_roas,
        "total_ntb_roas": total_ntb_roas,
        "ctr": ctr,
        "snssr": snssr,
        "roas": roas,
        "total_roas": total_roas,
        "ecpc": ecpc,
        "purchase_rate": purchase_rate,
        "ppd": ppd,
        "cpp": cpp,
        "dpvr": dpvr,
        "percent_of_purchases_total_ntb": percent_of_purchases_total_ntb,
        "cvr_clickthroughs": cvr_clickthroughs,
        "brand_search_rate": brand_search_rate,
        "viewability_rate": viewability_rate
    }





def percent_of_purchases_NTB(num_of_first_time_ourchases, total_purchases):
    try:
        quotient = (num_of_first_time_ourchases * 100) / total_purchases
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def ecpm (total_ad_spend, impressions):
    try:
        quotient = (total_ad_spend * 1000)/ impressions
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def ntb_roas (rev_from_new_cus, total_ad_spend):
    try:
        quotient = rev_from_new_cus / total_ad_spend
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def total_ntb_roas (total_rev_from_new_cus, total_ad_spend):
    try:
        quotient = total_rev_from_new_cus / total_ad_spend
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def ctr (clickthroughs, number_of_views):
    try:
        quotient = clickthroughs*100 / number_of_views
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def snssr (snss, impressions):
    try:
        quotient = snss / impressions
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0


def roas (product_sales, ad_spend):
    try:
        quotient = product_sales / ad_spend
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def total_roas (revenue, total_ad_spend):
    try:
        quotient = revenue / total_ad_spend
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0


def ecpc (total_ad_spend, clickthroughs):
    try:
        quotient = (total_ad_spend) / clickthroughs
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def purchase_rate (total_purchases, impreessions):
    try:
        quotient = total_purchases * 100 /impreessions
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def ppd (total_purchases, total_ad_spend):
    try:
        quotient = total_purchases / total_ad_spend
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def cpp (total_Ad_spend, total_purchases):
    try:
        quotient = total_Ad_spend / total_purchases
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def dpvr (totalDetailPageViews14d, impressions):
    try:
        quotient = totalDetailPageViews14d / impressions
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0


def percent_of_purchases_total_NTB(totalNewToBrandPurchases14d, total_purchases):
    try:
        quotient = (totalNewToBrandPurchases14d * 100) / total_purchases
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def  cvr_clickthroughs (clickThroughs, purchases14d):
    try:
        quotient = clickThroughs / purchases14d
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0

def brand_search_rate (brandSearch14d, impressions):
    try:
        quotient = brandSearch14d / impressions
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0
    

def viewability_rate (viewableImpressions, measurableImpressions):
    try:
        quotient = viewableImpressions / measurableImpressions
        return round (quotient, 4)
    except ZeroDivisionError:
        print("Error: Cannot divide by zero.")
        return 0


def metricsMapping(key):
    # NOT FUNCTION METRICS MAPPING
    data = {
        "total_cost": '"totalCost"',
        "impressions": '"impressions"',
        "clickthroughs": '"clickThroughs"',
        "dpv": '"dpv14d"',
        "gross_impressions": '"grossImpressions"',
        "atc": '"atc14d"',
        "total_snss": '"totalSubscribeAndSaveSubscriptions14d"',
        "ntb_purchases": '"newToBrandPurchases14d"',
        "ntb_sales": '"newToBrandProductSales14d"',
        "total_ntb_purchases": '"totalNewToBrandPurchases14d"',
        "total_ntb_product_sales": '"totalNewToBrandProductSales14d"',
        "subscription": '"subscribe14d"',
        "product_sales": '"sales14d"',
        "total_sales": '"totalSales14d"',
        "ecpp": '"eCPP14d"',
        "brand_search": '"brandSearch14d"',
        "brand_search_rate": '"brandSearchRate14d"',
        "purchases": '"purchases14d"',
        "total_purchases": '"totalPurchases14d"',
        "total_dpv": '"totalDetailPageViews14d"',
        "units_sold": '"unitsSold14d"',
        "total_units_sold": '"totalUnitsSold14d"',
        "total_atc":"totalAddToCart14d",
        "viewability_rate": '"viewabilityRate"',
        "measurable_impressions": "measurableImpressions",
        "viewable_impressions" : "viewableImpressions"
    }

    if key not in data:
        raise ValueError("Invalid Column passed")
    return data[key]

# print(metricsMapping("total_sales"))

def metricsMapping2(col1_value):
    # FUNCTION MRTRICS MAPPING
    mapping = {
        "dpvr": ("totalDetailPageViews14d", "impressions"),
        "percent_of_purchases_ntb": ("newToBrandPurchases14d", "totalPurchases14d"),
        "percent_of_purchases_total_ntb": ("totalNewToBrandPurchases14d", "totalPurchases14d"),
        "cvr_clickthroughs": ("clickThroughs", "purchases14d"),
        "ecpm": ("totalCost", "impressions"),
        "ntb_roas": ("newToBrandProductSales14d", "totalCost"),
        "total_ntb_roas": ("totalNewToBrandProductSales14d", "totalCost"),
        "ctr": ("clickThroughs", "impressions"),
        "snssr": ("totalSubscribeAndSaveSubscriptions14d", "impressions"),
        "roas": ("sales14d", "totalCost"),
        "total_roas": ("totalSales14d", "totalCost"),
        "ecpc": ("totalCost", "clickThroughs"),
        "purchase_rate": ("totalPurchases14d", "grossImpressions"),
        "ppd": ("totalPurchases14d", "totalCost"),
        "cpp": ("totalCost", "totalPurchases14d"),
        "brand_search_rate" : ("brandSearch14d", "impressions"),
        "viewability_rate" : ("viewableImpressions","measurableImpressions")
    }

    try:
        column_values = mapping[col1_value]
        return column_values
    except KeyError:
        print(f"Error: Column '{col1_value}' does not exist.")
        return (None, None)
