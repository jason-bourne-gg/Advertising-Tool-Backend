from database import db
from datetime import datetime
from sqlalchemy import JSON
from dotenv import load_dotenv
import os


load_dotenv()
env = os.environ.get("ENV")




user_region = db.Table('user_region',
    db.Column ("id", db.Integer, primary_key=True), 
    db.Column ('user_id', db.Integer, db.ForeignKey('user_details.id')),
    db.Column ('region_id', db.Integer, db.ForeignKey('region.id'))
) 

user_brand = db.Table('user_brand',
    db.Column ("id", db.Integer, primary_key=True), 
    db.Column ('user_id', db.Integer, db.ForeignKey('user_details.id')),
    db.Column ('brand_id', db.Integer, db.ForeignKey('brand.id'))
)

user_campaign_type = db.Table('user_campaign_type',
    db.Column ("id", db.Integer, primary_key=True), 
    db.Column ('user_id', db.Integer, db.ForeignKey('user_details.id')),
    db.Column ('campaign_type_id', db.Integer, db.ForeignKey('campaign_type.id'))
)

user_target_platform = db.Table('user_target_platform',
    db.Column ("id", db.Integer, primary_key=True), 
    db.Column ('user_id', db.Integer, db.ForeignKey('user_details.id')),
    db.Column ('target_platform_id', db.Integer, db.ForeignKey('target_platform.id'))
)

class UserDetails (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    name = db.Column (db.String(100))
    email = db.Column (db.String(500),  nullable =False, unique = True)
    role = db.Column (db.String(50))
    created_on = db.Column (db.DateTime, default= datetime.utcnow)
    access_granter = db.Column (db.String(100), nullable =False)
    access_granted_on = db.Column (db.DateTime, default= datetime.utcnow)

    campaigns = db.relationship ('Campaign', backref= 'user_details', lazy = "select")
    regions = db.relationship('Region', secondary = user_region, backref = 'users_allowed_in_region', lazy = "select") 
    brands = db.relationship('Brand', secondary = user_brand, backref = 'users_allowed_for_brands', lazy = "select") 
    campaign_type = db.relationship('CampaignType', secondary = user_campaign_type, backref = 'users_allowed_for_campaign_type', lazy = "select") 
    target_platform = db.relationship('TargetPlatform', secondary = user_target_platform, backref = 'users_allowed_for_target_platform', lazy = "select") 
    campaign_drafts = db.relationship ('CampaignDrafts', backref = 'user_details', lazy = "select" )

class Campaign (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    order_id = db.Column (db.String(50), unique =True)
    campaign_name = db.Column (db.String(500),  nullable =False)
    target_platform_id = db.Column (db.Integer,db.ForeignKey('target_platform.id'))
    campaign_type_id = db.Column (db.Integer,db.ForeignKey('campaign_type.id') )
    brand_id = db.Column (db.Integer, db.ForeignKey('brand.id'))
    region_id = db.Column (db.Integer, db.ForeignKey('region.id'))
    goal_goal_kpi_id = db.Column (db.Integer, db.ForeignKey('goal_goal_kpi.id'))
    goal_kpi =db.Column (db.String(50), nullable =False)
    context_list = db.Column (JSON, nullable =False ) 
    product_tracking_list = db.Column (db.String(50))
    start_time = db.Column (db.DateTime, nullable =False) #this is date recieved from user on frontend
    end_time = db.Column (db.DateTime, nullable =False) #this is date recieved from user on frontend
    audience_ids = db.Column (JSON)
    total_budget = db.Column (db.Float, nullable =False)
    max_change_in_budget = db.Column (db.Float, nullable =False)
    campaign_status = db.Column (db.String(50), nullable =False)
    created_by_email = db.Column (db.String(500), db.ForeignKey('user_details.email'))
    created_on = db.Column (db.DateTime, nullable =False, default = datetime.utcnow)
    modified_on = db.Column (db.DateTime,nullable =False,  default = datetime.utcnow)
    orderPO_number = db.Column (db.String(50))
    domain_names = db.Column (JSON) 
    suggestions = db.Column (JSON)
    request_id = db.Column (db.String(50))
    order_budget = db.Column (JSON) #recieved from DS request payload
    budget_optimization = db.Column (JSON) #recieved from DS request payload
    frequency_cap = db.Column (JSON)

    # one to many relationships
    line_items = db.relationship ('LineItems' , backref = 'campaign', lazy = "select" )
    # brand_region = db.relationship ('brand_region', backref = 'campaign')
    line_item_metric = db.relationship ('LineItemMetrics', backref = 'campaign', lazy = "select")

    # one to one relationships (uselist = Flase is removed as it was not working)
    campaign_recommendations = db.relationship ('CampaignRecommendations', backref = 'campign', lazy = "select" )

   

class LineItems (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    order_id = db.Column (db.String(50), db.ForeignKey('campaign.order_id'))
    line_item_id = db.Column (db.String(50), nullable =False, unique = True)
    line_item_type = db.Column (db.String(50))
    line_item_name = db.Column (db.String(500), nullable =False)
    start_time = db.Column (db.DateTime)
    end_time = db.Column (db.DateTime)
    line_item_classification = db.Column (JSON)
    frequency_cap = db.Column(JSON)
    targeting = db.Column(JSON)
    bidding = db.Column(JSON)
    budget = db.Column(JSON)
    optimization = db.Column(JSON)
    creatives = db.Column(JSON)

    # one to one relationships 
    line_item_metric = db.relationship ('LineItemMetrics', backref = 'line_item', lazy = "select")

    # for some reason uselist = false is not working, hence making one to many relationships 
    campaign_recommendations = db.relationship ('CampaignRecommendations', backref = 'line_item', lazy = "select" )

class LineItemMetrics(db.Model):
    __tablename__ = "de_campaign_performance"

    # id = db.Column(db.Integer, primary_key=True, nullable = False)
    line_item_id = db.Column (db.String(50), db.ForeignKey('line_items.line_item_id'), primary_key=True )
    line_item_name = db.Column (db.String(500), primary_key=True)
    order_id = db.Column (db.String(50),db.ForeignKey('campaign.order_id'), primary_key=True)
    atc14d = db.Column(db.Integer)
    brandSearch14d = db.Column(db.Integer)
    brandSearchRate14d = db.Column(db.Float)
    clickThroughs = db.Column(db.Integer)
    date = db.Column(db.DateTime, primary_key=True)
    dpv14d = db.Column(db.Integer)
    eCPP14d = db.Column(db.Float)
    grossImpressions = db.Column(db.Integer)
    impressions = db.Column(db.Integer)
    newToBrandProductSales14d = db.Column(db.Float)
    newToBrandPurchases14d = db.Column(db.Integer)
    purchases14d = db.Column(db.Integer)
    sales14d = db.Column(db.Float)
    subscribe14d = db.Column(db.Integer)
    totalAddToCart14d = db.Column(db.Integer)
    totalCost = db.Column(db.Float)
    totalDetailPageViews14d = db.Column(db.Integer)
    totalNewToBrandProductSales14d = db.Column(db.Float)
    totalNewToBrandPurchases14d = db.Column(db.Integer)
    totalPurchases14d = db.Column(db.Integer)
    totalSales14d = db.Column(db.Float)
    totalSubscribeAndSaveSubscriptions14d = db.Column(db.Integer)
    totalUnitsSold14d = db.Column(db.Integer)
    unitsSold14d = db.Column(db.Integer)
    viewabilityRate = db.Column(db.Float)
    viewableImpressions = db.Column(db.Integer)
    measurableImpressions = db.Column(db.Integer)
    orderBudget = db.Column(db.Float)


class CampaignType (db.Model):
    id = db.Column (db.Integer, primary_key = True)
    campaign_type = db.Column (db.String(50), nullable =False)
    target_platform_id = db.Column (db.Integer, db.ForeignKey ('target_platform.id'))


    # one to many
    campaigns = db.relationship ('Campaign', backref = 'campaign_type', lazy = "select" )



class TargetPlatform (db.Model):
    id = db.Column (db.Integer, primary_key =True)
    platform = db.Column (db.String(50), nullable =False)

    # one to many
    campaigns = db.relationship ('Campaign', backref = 'target_platform', lazy = "select" )
    campaign_types = db.relationship ('CampaignType', backref = 'target_platform', lazy = "select")

    # amzondispllay, amazonsearch

class CampaignRecommendations (db.Model):
    __tablename__ = "de_recommendations"

    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    order_id = db.Column (db.String(50), db.ForeignKey('campaign.order_id'))
    line_item_id = db.Column (db.String(50), db.ForeignKey('line_items.line_item_id') )
    brand_id = db.Column (db.Integer, db.ForeignKey('brand.id'))
    recommendation_text = db.Column (db.String(1000))
    status = db.Column (db.String(50))
    context = db.Column (db.String(500))
    recommendation_object = db.Column (db.String(500))
    date_of_generation = db.Column (db.DateTime)
    date_of_user_action = db.Column (db.DateTime)
    flag = db.Column (db.String(100))


class RecommendedContexts (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    region_id = db.Column (db.Integer, db.ForeignKey('region.id')) 
    brand_id = db.Column (db.Integer, db.ForeignKey('brand.id'))
    context = db.Column (db.String(50))


# assocaiation table for brand and region
brand_region = db.Table('brand_region',
    db.Column ("id", db.Integer, primary_key=True),                     
    db.Column ('brand_id', db.Integer, db.ForeignKey('brand.id')),
    db.Column ('region_id', db.Integer, db.ForeignKey('region.id'))
)

class Brand (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    brand_code = db.Column (db.String(5000))
    brand_name = db.Column (db.String(50), nullable=False)

    # one to many
    campaigns = db.relationship ('Campaign', backref = 'brand', lazy = "select" )
    regions = db.relationship('Region', secondary = brand_region, backref = 'brands_in_region', lazy = "select")
    suggestions = db.relationship ('Suggestion', backref = 'brand', lazy ='select')
    recommendedcontexts = db.relationship ('RecommendedContexts', backref = 'brand', lazy ='select')
    recommendations = db.relationship ('CampaignRecommendations', backref = 'brand', lazy = "select" )

class Region (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    region_code = db.Column (db.String(50))
    region_name = db.Column (db.String(50), nullable=False)
    
    # ome to many
    campaigns = db.relationship ('Campaign', backref = 'region', lazy = "select" )
    suggestions = db.relationship ('Suggestion', backref = 'region', lazy ='select')
    recommendedcontexts = db.relationship ('RecommendedContexts', backref = 'region', lazy ='select')


class GoalGoalKPI (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    goal_name = goal_name = db.Column (db.String(50), nullable =False)
    goalKPI_list = db.Column (JSON, nullable =False)

    # one to many relationship
    campaigns = db.relationship ('Campaign' , backref= 'goal_goal_kpi', lazy = "select")
    


class AudienceId (db.Model):
    __tablename__ = "de_audience"

    # id = db.Column (db.Integer, primary_key =True,  nullable =False)
    audienceId = db.Column (db.String(50), primary_key =True)
    audienceName = db.Column ((db.String(300)))
    status =  db.Column (db.String(100))
    category = db.Column (db.String(100))

    # 1 to many with campaign || many to many I guess
    # for now just making an API to display list on slection of ids, not making any linking with campigns 
    # campaigns = db.relationship('Campaign', backref = 'audience_ids', lazy = 'select') 


class Suggestion (db.Model):
    __tablename__ = "de_brand_settings"
    
    # id = db.Column (db.Integer, primary_key =True,  nullable =False)
    region_id = db.Column (db.Integer, db.ForeignKey('region.id'))
    brand_id = db.Column (db.Integer, db.ForeignKey('brand.id'))
    context = db.Column (db.String(200), primary_key =True)
    bid = db.Column (db.Float )
    viewability = db.Column (db.String(50))
    frequency_cap_days = db.Column (db.Float)
    frequency_cap_amount = db.Column (db.Float)
    weekly_budget = db.Column (db.Float)
    line_item_count = db.Column (db.Integer)
    DMA_exclude = db.Column (db.String(50))
    last_updated_on = db.Column (db.DateTime, default = datetime.utcnow)

class DomainNames (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    domain_id = db.Column (db.String(50))
    domain_name = db.Column ((db.String(100)))

    # Many to many with camp I guess, rn not addeding relationship, coz not needed now

class OrderPONumber (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    orderPOnumber = db.Column (db.String(50))
    is_default = db.Column (db.String(50))

class CustomContext (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    line_item_type = db.Column (JSON) 
    device_type = db.Column (JSON) 
    supply_source = db.Column (JSON) 

class ColumnLineItems (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    delivery = db.Column (JSON)    
    performance = db.Column (JSON) 

class AmazonAPICallLogs(db.Model):
    # id = db.Column (db.Integer, primary_key =True,  nullable =False)
    timestamp = db.Column (db.DateTime, default = datetime.utcnow, primary_key =True)
    user_email = db.Column (db.String(50))
    payload = db.Column (JSON)
    response = db.Column (JSON)

class MetricsMapping (db.Model):
    id = db.Column (db.Integer, primary_key =True,  nullable =False)
    metric_column_name = db.Column (db.String(50))
    metric_column_label = db.Column (db.String(50))

class DummyTable (db.Model):
    # id = db.Column (db.Integer, primary_key =True,  nullable =False)
    recommended_context = db.Column (db.String(50), primary_key =True)
    user_bid_value = db.Column (db.Float)

class CampaignDrafts (db.Model):
    id = db.Column (db.Integer, primary_key =True)
    campaign_name = db.Column (db.String(500), nullable =False )
    brand = db.Column (JSON ) 
    region = db.Column (JSON ) 
    goal = db.Column (JSON ) 
    goal_kpi =db.Column (db.String(50))
    context_list = db.Column (JSON ) 
    product_tracking_list = db.Column (JSON)
    start_time = db.Column (db.DateTime) #this is date recieved from user on frontend
    end_time = db.Column (db.DateTime) #this is date recieved from user on frontend
    audience_ids = db.Column (JSON)
    total_budget = db.Column (db.Float)
    max_change_in_budget = db.Column (db.Float)
    campaign_status = db.Column (db.String(50))
    created_by_email = db.Column (db.String(500), db.ForeignKey('user_details.email'))
    created_on = db.Column (db.DateTime, default = datetime.utcnow)
    modified_on = db.Column (db.DateTime,  default = datetime.utcnow)
    orderPO_number = db.Column (db.String(50))
    domain_names = db.Column (JSON) 
    suggestion = db.Column (JSON)