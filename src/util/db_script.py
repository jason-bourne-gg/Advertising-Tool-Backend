from database import db
from datetime import date
from models import *
import pandas as pd
import sqlalchemy.exc as sa_exc
from dotenv import load_dotenv
import os
from sqlalchemy import Table


load_dotenv()
env = os.environ.get("ENV")


def createdb():
    print("\n Dropping all previous created tables \n")
    db.reflect()
    db.drop_all()
    print("\n creating new tables \n")
    db.create_all()
    db.session.commit()
    print("\n All tables created \n")

    print("\n Running script to laod data and relationships \n")

    brand1 = Brand(brand_code="Brand1", brand_name="NUTRAMIGEN")
    brand2 = Brand(brand_code="Brand2", brand_name="ENFAMOM")
    brand3 = Brand(brand_code="Brand3", brand_name="PURAMINO")
    # brand4 = Brand (brand_code = "LYS78", brand_name = "LYSOL")

    db.session.add_all([brand1, brand2, brand3])
    db.session.commit()

    region1 = Region(region_code="001", region_name="NORTH AMERICA")
    region2 = Region(region_code="002", region_name="LATAM")
    region3 = Region(region_code="003", region_name="ASIA PACIFIC")
    # region4 = Region (region_code = "004", region_name = "EUROPE")

    db.session.add_all([region1, region2, region3])
    db.session.commit()

# Define data for all the rows
    user_data = [   
        {
            "name": "Aniket",
            "email": "aniket.charjan@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 8, 873000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Debamitra",
            "email": "debamitram@sigmoidanalytics.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 8, 873000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Ravindra",
            "email": "Ravindra.Singh3@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 8, 873000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Shagunpreet",
            "email": "shagunpreet.singh@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 8, 873000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Sabrina",
            "email": "sabrina.brelvi@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 8, 883000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Imteaz",
            "email": "imteaz.ahamed@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 8, 987000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Joseph",
            "email": "joseph.stewart2@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 37000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Arun",
            "email": "arun.kumard@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 63000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Devansh",
            "email": "devansh.parikh@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 90000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Anurag",
            "email": "anurag.srivastava@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 157000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Bhargav",
            "email": "bhargav.kar@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 183000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Vikash",
            "email": "vikash.choudhary@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 207000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Abhishek",
            "email": "abhishek.mishra@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 293000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Shyam",
            "email": "shyam.prasad@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 390000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Prakriti",
            "email": "prakriti.patra@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 413000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Ankit",
            "email": "ankit.gupta4@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 467000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Aswinkumar",
            "email": "aswinkumar.ks@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 490000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Tuncay",
            "email": "sarp.tuncay@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 34, 56),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Katherine",
            "email": "katherine.marte@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 34, 56),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Macklan",
            "email": "macklan.one@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 34, 56),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 20, 12, 34, 56),
        },
        {
            "name": "Deb Apriyad",
            "email": "Deb.Apriyad@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 27, 6, 52, 0, 473000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 27, 6, 52, 0, 473000),
        },
        {
            "name": "Marcus",
            "email": "grant.marcus@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 20, 12, 26, 9, 293000),
            "access_granter": "Arun",
            "access_granted_on": datetime(2023, 7, 28, 6, 49, 22, 197000),
        },
        {
            "name": "Debamitra Mukherjee",
            "email": "Debamitra.Mukherjee@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 7, 28, 7, 25, 39, 837000),
            "access_granter": "Ravindra",
            "access_granted_on": datetime(2023, 7, 28, 7, 25, 39, 837000),
        },
        {
            "name": "Gupta, Kirti (Contractor)",
            "email": "Kirti.Gupta@reckitt.com",
            "role": "admin",
            "created_on": datetime(2023, 8, 23, 6, 44, 31, 300000),
            "access_granter": "Vikash",
            "access_granted_on": datetime(2023, 8, 23, 6, 44, 31, 300000),
        },
        {
            "name": "Rahul Jassal",
            "email": "Rahul.Jassal@reckitt.com",
            "role": "user",
            "created_on": datetime(2023, 9, 19, 20, 15, 55, 730000),
            "access_granter": "Shagunpreet",
            "access_granted_on": datetime(2023, 9, 19, 20, 15, 55, 730000),
        },
    ]

    # giving access to all uses added above
    for data in user_data:
        user_object = UserDetails(**data)
        db.session.add(user_object)

        # Commit all the changes to the database
        db.session.commit()

        user_object.regions.extend((region1, region2, region3))
        user_object.brands.extend((brand1, brand2, brand3))
        db.session.commit()

    goal1 = GoalGoalKPI(goal_name="AWARENESS", goalKPI_list=[
                        "COST_PER_VIDEO_COMPLETION", "REACH", "VIDEO_COMPLETION_RATE"])
    goal2 = GoalGoalKPI(goal_name="PURCHASES_ON_AMAZON", goalKPI_list=[
                        "RETURN_ON_AD_SPEND", "TOTAL_RETURN_ON_AD_SPEND"])
    goal3 = GoalGoalKPI(goal_name="ENGAGEMENT_WITH_MY_AD", goalKPI_list=[
                        "CLICK_THROUGH_RATE", "COST_PER_CLICK", "COST_PER_VIDEO_COMPLETION", "VIDEO_COMPLETION_RATE"])
    goal4 = GoalGoalKPI(goal_name="CONSIDERATIONS_ON_AMAZON", goalKPI_list=[
                        "COST_PER_DETAIL_PAGE_VIEW", "DETAIL_PAGE_VIEW_RATE"])
    goal5 = GoalGoalKPI(goal_name="PURCHASES_ON_OFF_AMAZON", goalKPI_list=[
                        "COMBINED_RETURN_ON_AD_SPEND"])

    db.session.add_all([goal1, goal2, goal3, goal4, goal5])
    db.session.commit()

    target_platform1 = TargetPlatform(platform="AMAZON")

    db.session.add_all([target_platform1])
    db.session.commit()

    campaign_type1 = CampaignType(campaign_type="AMAZON-SEARCH")
    campaign_type2 = CampaignType(campaign_type="AMAZON-DISPLAY")

    db.session.add_all([campaign_type1, campaign_type2])
    db.session.commit()

   
    # db.session.add_all([camp1, camp2])
    # db.session.commit()


   
    maping1 = MetricsMapping(metric_column_name="atc",
                             metric_column_label="ATC")
    maping2 = MetricsMapping(
        metric_column_name="brand_search", metric_column_label="BRAND SEARCH")
    maping3 = MetricsMapping(
        metric_column_name="brand_search_rate", metric_column_label="BRAND SEARCH RATE")
    maping4 = MetricsMapping(
        metric_column_name="clickthroughs", metric_column_label="CLICKTHROUGHS")
    maping5 = MetricsMapping(metric_column_name="dpv",
                             metric_column_label="DPV")
    maping6 = MetricsMapping(metric_column_name="ecpp",
                             metric_column_label="ECPP")
    maping7 = MetricsMapping(
        metric_column_name="gross_impressions", metric_column_label="GROSS IMPRESSIONS")
    maping8 = MetricsMapping(
        metric_column_name="impressions", metric_column_label="IMPRESSIONS")
    maping9 = MetricsMapping(
        metric_column_name="ntb_purchases", metric_column_label="NTB PURCHASES")
    maping10 = MetricsMapping(
        metric_column_name="ntb_sales", metric_column_label="NTB SALES")
    maping11 = MetricsMapping(
        metric_column_name="product_sales", metric_column_label="PRODUCT SALES($)")
    maping12 = MetricsMapping(
        metric_column_name="purchases", metric_column_label="PURCHASES")
    maping13 = MetricsMapping(
        metric_column_name="subscription", metric_column_label="SUBSCRIPTIONS")
    maping14 = MetricsMapping(
        metric_column_name="total_cost", metric_column_label="TOTAL COST($)")
    maping15 = MetricsMapping(metric_column_name="total_ntb_product_sales",
                              metric_column_label="TOTAL NTB PRODUCT SALES")
    maping16 = MetricsMapping(
        metric_column_name="total_ntb_purchases", metric_column_label="TOTAL NTB PURCHASES")
    maping17 = MetricsMapping(
        metric_column_name="total_purchases", metric_column_label="TOTAL PURCHASES")
    maping18 = MetricsMapping(
        metric_column_name="total_snss", metric_column_label="TOTAL SNSS")
    maping19 = MetricsMapping(
        metric_column_name="total_subscription", metric_column_label="TOTAL SUBSCRIPTION")
    maping20 = MetricsMapping(
        metric_column_name="total_atc", metric_column_label="TOTAL ATC")
    maping21 = MetricsMapping(
        metric_column_name="total_dpv", metric_column_label="TOTAL DPV")
    maping22 = MetricsMapping(
        metric_column_name="total_sales", metric_column_label="TOTAL SALES")
    maping23 = MetricsMapping(
        metric_column_name="total_units_sold", metric_column_label="TOTAL UNITS SOLD")
    maping24 = MetricsMapping(
        metric_column_name="units_sold", metric_column_label="UNITS SOLD")
    maping25 = MetricsMapping(
        metric_column_name="viewability_rate", metric_column_label="VIEWABILITY RATE")

    maping26 = MetricsMapping(
        metric_column_name="dpvr", metric_column_label="DPVR")
    maping27 = MetricsMapping(
        metric_column_name="percent_of_purchases_ntb", metric_column_label="% OF PURCHASES NTB ")
    maping28 = MetricsMapping(metric_column_name="percent_of_purchases_total_ntb",
                              metric_column_label="% OF PURCHASES TOTAL NTB")
    maping29 = MetricsMapping(
        metric_column_name="cvr_clickthroughs", metric_column_label="CVR CLICKTHROUGHS")
    maping30 = MetricsMapping(
        metric_column_name="ecpm", metric_column_label="ECPM")
    maping31 = MetricsMapping(
        metric_column_name="ntb_roas", metric_column_label="NTB ROAS")
    maping32 = MetricsMapping(
        metric_column_name="total_ntb_roas", metric_column_label="TOTAL NTB ROAS")
    maping33 = MetricsMapping(metric_column_name="ctr",
                              metric_column_label="CTR")
    maping34 = MetricsMapping(
        metric_column_name="snssr", metric_column_label="SNSSR")
    maping35 = MetricsMapping(
        metric_column_name="roas", metric_column_label="ROAS")
    maping36 = MetricsMapping(
        metric_column_name="total_roas", metric_column_label="TOTAL ROAS")
    maping37 = MetricsMapping(
        metric_column_name="ecpc", metric_column_label="ECPC")
    maping38 = MetricsMapping(
        metric_column_name="purchase_rate", metric_column_label="PURCHASE RATE")
    maping39 = MetricsMapping(metric_column_name="cpp",
                              metric_column_label="CPP")
    maping40 = MetricsMapping(metric_column_name="ppd",
                              metric_column_label="PPD")

    maping41 = MetricsMapping(
        metric_column_name="line_item_name", metric_column_label="LINE ITEM NAME")
    maping42 = MetricsMapping(
        metric_column_name="line_item_type", metric_column_label="LINE ITEM TYPE")
    maping43 = MetricsMapping(
        metric_column_name="line_item_id", metric_column_label="LINE ITEM ID")
    maping44 = MetricsMapping(metric_column_name="bid",
                              metric_column_label="BID")
    maping45 = MetricsMapping(
        metric_column_name="start_time", metric_column_label="START TIME")
    maping46 = MetricsMapping(
        metric_column_name="end_time", metric_column_label="END TIME")
    maping47 = MetricsMapping(
        metric_column_name="measurable_impressions", metric_column_label="MEASURABLE IMPRESSIONS")
    maping48 = MetricsMapping(
        metric_column_name="viewable_impressions", metric_column_label="VIEWABLE IMPRESSIONS")

    db.session.add_all([maping1, maping2, maping3, maping4, maping5, maping6, maping7, maping8, maping9, maping10, maping11, maping12, maping13, maping14, maping15, maping16, maping17, maping18, maping19, maping20, maping21, maping22, maping23, maping24, maping25, maping26, maping27, maping28,
                        maping29, maping30, maping31, maping32, maping33, maping34, maping35, maping36, maping37, maping38, maping39, maping40, maping41, maping42, maping43, maping44, maping45, maping46, maping47, maping48])
    db.session.commit()

    context1 = RecommendedContexts(context="AMD | APP | AZOO")
    context2 = RecommendedContexts(context="SD | DTMB | AZOO")
    context3 = RecommendedContexts(context="AAP | APP | 3P")
    context4 = RecommendedContexts(context="SD | DTMB | 3P")
    context5 = RecommendedContexts(context="AMD | APP | AZOO")
    context6 = RecommendedContexts(context="SD | DTMB | AZOO")
    context7 = RecommendedContexts(context="AAP | APP | 3P")
    context8 = RecommendedContexts(context="AAP | APP | AZPS")
    context9 = RecommendedContexts(context="AMD | APP | AZOO")
    context10 = RecommendedContexts(context="SD | DTMB | AZOO")
    context11 = RecommendedContexts(context="SD | DTMB | 3P")

    db.session.add_all([context1, context2, context3, context4, context5,
                       context6, context7, context8, context9, context10, context11])
    db.session.commit()

    domainName1 = DomainNames(domain_id="d8badc86-1bbd-00ce-7e30-09aedc619e27",
                              domain_name="Sensitive Retargeting Domain Low CTR")
    domainName2 = DomainNames(domain_id="d2badc89-c73d-6d19-26dd-5193cac945ae",
                              domain_name="NeuroPro GE Retagreting_Domain_Low CTR")
    domainName3 = DomainNames(domain_id="4cbadc8b-9269-5170-aa5a-70e44f3997d3",
                              domain_name="AR Consideration_Domains_Low CTR")
    domainName4 = DomainNames(domain_id="5abadc8d-bc9f-abe2-fe36-d440d9272be9",
                              domain_name="Nutramigen Retargeting Domains Low ROAS")
    domainName5 = DomainNames(domain_id="60badc92-f541-7878-b3e7-db09b6bffd44",
                              domain_name="Nutramigen Consideration Low ROAS")

    db.session.add_all(
        [domainName1, domainName2, domainName3, domainName4, domainName5])
    db.session.commit()

    orderponumber1 = OrderPONumber(orderPOnumber="80005566307")
    db.session.add_all([orderponumber1])
    db.session.commit()

    customcontext1 = CustomContext(line_item_type=["SD"], device_type=["DTMB"], supply_source=["AZOO", "AZPS", "IMDB", "3P", "3P AZPS", "3P AZOO",
                                   "3P IMDB", "AZPS AZOO", "AZPS IMDB", "AZOO IMDB", "3P AZPS AZOO", "3P AZPS IMDB", "3P AZOO IMDB", "AZPS AZOO IMDB", "3P AZPS AZOO IMDB"])
    customcontext2 = CustomContext(line_item_type=["AMD"], device_type=[
                                   "APP"], supply_source=["AZOO", "IMDB", "AZOO IMDB"])
    customcontext3 = CustomContext(line_item_type=["AAP"], device_type=["APP"], supply_source=[
                                   "3P AZPS", "AZPS", "IMDB", "3P", "3P IMDB", "AZPS IMDB", "3P AZPS IMDB"])

    db.session.add_all((customcontext1, customcontext2, customcontext3))
    db.session.commit()

    column1 = ColumnLineItems(delivery=["bid", "ecpm", "total_cost", "impressions", "clickthroughs", "ctr", "start_time", "end_time"],
                              performance=["total_roas", "atc", "purchases", "total_purchases", "product_sales", "total_sales", "ppd", "cpp"])

    db.session.add(column1)
    db.session.commit()



    # Relationships
    # one to many relationships, but trying here 1 to 1


    region1.brands_in_region.extend((brand1, brand2, brand3))






    # camp2.line_items.append((item3)) #....becasue camp 2 is initilizing and it cannot have line items
    # camp1.line_item_metric.extend ((metric1,metric2,metric3))

    # adding foregin keys of line items to metric table
    # item1.line_item_metric.append ((metric1))
    # item2.line_item_metric.append ((metric2))
    # item3.line_item_metric.append ((metric3))
    # print(item1.line_item_metric[0].impressions)
    # print(metric1.line_item.budget)

    brand1.recommendedcontexts.extend((context1, context2, context3, context4))
    brand3.recommendedcontexts.extend((context5, context6))
    brand2.recommendedcontexts.extend(
        (context7, context8, context9, context10, context11))
    # print(context1.brand.brand_name)
    # print(brand1.recommendedcontexts[0].context)

    region1.recommendedcontexts.extend((context1, context2, context3, context4,
                                       context5, context6, context7, context8, context9, context10, context11))

    # # AccessControl Relationships
    # region1.users_allowed_in_region.extend((user1, user2, user3))
    # brand1.users_allowed_for_brands.extend((user1, user2, user3))
    # campaign_type1.users_allowed_for_campaign_type.extend(
    #     (user1, user2, user3))
    # target_platform1.users_allowed_for_target_platform.extend(
    #     (user1, user2, user3))

    # user1.brands.extend((brand1, brand2, brand3))
    # user2.brands.extend((brand1, brand2))
    # user3.brands.extend((brand1, brand3))
    # user4.brands.extend((brand1, brand3))

    # user1.regions.extend((region1, region2, region3))
    # user3.regions.extend((region1, region3))
    # user2.regions.extend((region1, region2))
    # user4.regions.append((region1))

    # db.session.commit()

    # print(suggestion1.brand.brand_name)
