""" IMPORTING DIFFERENT PACKAGES AND LIBRARIES """
import logging
import os
import urllib
import secrets
from pathlib import Path
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
from flask_session_fs import Session
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from sqlalchemy import inspect
from pytz import timezone,utc  # Import the timezone functions
import sqlalchemy
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from settings.config import db_connection_string

""" IMPORTING FUNTIONS AND INSTANCES FROM OTHER FILES """
from appcache import cache
from database import db
from apis.user import User
from settings.config import app_setting, db_driver, db_database, db_password, db_server, db_username
from util.db_script import createdb

from apis.auth import auth_blueprint
from apis.user import user_blueprint
from apis.createCampaignAPIs.brands import brand_blueprint
from apis.createCampaignAPIs.regions import region_blueprint
from apis.currentCampaignAPIs.getcampaigns import campaign_blueprint
from apis.createCampaignAPIs.getaudienceids import audienceids_blueprint
from apis.createCampaignAPIs.getsuggestions import suggestions_blueprint
from apis.currentCampaignAPIs.getlineitems import lineitems_blueprint
from apis.createCampaignAPIs.recommendedcontext import recommendedcontext_blueprint
from apis.createCampaignAPIs.goalkpis import goalkpis_blueprint
from apis.createCampaignAPIs.getbudget import budget_blueprint
from apis.createCampaignAPIs.storeproducttrackinglist import producttrackinglist_blueprint
from apis.createCampaignAPIs.getdomains import domainnames_blueprint
from apis.createCampaignAPIs.getorderPOnumber import orderPOnumber_blueprint
from apis.createCampaignAPIs.customcontext import customcontext_blueprint
from apis.createCampaignAPIs.downloadproductlist import downloadproducttrackinglist_blueprint
from apis.currentCampaignAPIs.getcolumns import column_blueprint
from apis.createCampaignAPIs.uploaddomainlist import uploaddomainlist_blueprint
from apis.createCampaignAPIs.downloaddomainlist import downloaddomainlist_blueprint
from apis.createCampaignAPIs.placeorderamazonAPI import placeorderonamazon_blueprint
from apis.currentCampaignAPIs.overallPerformance import overallperformance_blueprint
from apis.createCampaignAPIs.getdefaultproductlist import getdefaultproducttrackinglist_blueprint
from apis.createCampaignAPIs.getdefaultdomainList import getdefaultdomainlist_blueprint
from apis.currentCampaignAPIs.campaignScorecard import campaignscorecard_blueprint
from apis.currentCampaignAPIs.campaignRecommendation import campaignrecommendations_blueprint
from apis.currentCampaignAPIs.metricsMapping import metricsmapping_blueprint
from apis.adminPanel.generalSettings.MasterDomain import masterdomainlist_blueprint
from apis.adminPanel.generalSettings.MasterProduct import masterproductlist_blueprint
from apis.adminPanel.generalSettings.Creatives import creativesfile_blueprint
from apis.adminPanel.userSettings.usersettings import usersettings_blueprint
from apis.adminPanel.userSettings.getActiveUsers import active_users_blueprint
from apis.adminPanel.userSettings.getUserFromOkta import oktausers_blueprint
from apis.adminPanel.generalSettings.postBidValues import postbidvalues_blueprint
from apis.currentCampaignAPIs.editCampaign import editcampaign_blueprint
from apis.saveDraftAPIs.savedraft import savedraft_blueprint
from apis.currentCampaignAPIs.approveordenyreco import approvedenyreco_blueprint
from apis.adminPanel.userSettings.smallapis import smallapis_blueprint
from apis.expiredCampaignsAPIs.expiredCampaigns import expiredcampaigns_blueprint

""" LIST ALL BLUEPRINTS HERE """
def register_blueprints(app):
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(user_blueprint, url_prefix="/api")
    app.register_blueprint(brand_blueprint, url_prefix="/api")
    app.register_blueprint(region_blueprint, url_prefix="/api")
    app.register_blueprint(campaign_blueprint, url_prefix="/api")
    app.register_blueprint(audienceids_blueprint, url_prefix="/api")
    app.register_blueprint(suggestions_blueprint, url_prefix="/api")
    app.register_blueprint(lineitems_blueprint, url_prefix="/api")
    app.register_blueprint(recommendedcontext_blueprint, url_prefix="/api")
    app.register_blueprint(goalkpis_blueprint, url_prefix="/api")
    app.register_blueprint(budget_blueprint, url_prefix="/api")
    app.register_blueprint(producttrackinglist_blueprint, url_prefix="/api")
    app.register_blueprint(domainnames_blueprint, url_prefix="/api")
    app.register_blueprint(orderPOnumber_blueprint, url_prefix="/api")
    app.register_blueprint(customcontext_blueprint, url_prefix="/api")
    app.register_blueprint(downloadproducttrackinglist_blueprint, url_prefix="/api")
    app.register_blueprint(column_blueprint, url_prefix="/api")
    app.register_blueprint(uploaddomainlist_blueprint, url_prefix="/api")
    app.register_blueprint(downloaddomainlist_blueprint, url_prefix="/api")
    app.register_blueprint(placeorderonamazon_blueprint, url_prefix="/api")
    app.register_blueprint(overallperformance_blueprint, url_prefix="/api")
    app.register_blueprint(getdefaultproducttrackinglist_blueprint, url_prefix="/api")
    app.register_blueprint(getdefaultdomainlist_blueprint, url_prefix="/api")
    app.register_blueprint(campaignscorecard_blueprint, url_prefix="/api")
    app.register_blueprint(campaignrecommendations_blueprint, url_prefix="/api")
    app.register_blueprint(metricsmapping_blueprint, url_prefix="/api")
    app.register_blueprint(masterdomainlist_blueprint, url_prefix="/api")
    app.register_blueprint(masterproductlist_blueprint, url_prefix="/api")
    app.register_blueprint(creativesfile_blueprint, url_prefix="/api")
    app.register_blueprint(usersettings_blueprint, url_prefix="/api")
    app.register_blueprint(active_users_blueprint, url_prefix="/api")
    app.register_blueprint(oktausers_blueprint, url_prefix='/api')
    app.register_blueprint(postbidvalues_blueprint, url_prefix='/api')
    app.register_blueprint(editcampaign_blueprint, url_prefix='/api')
    app.register_blueprint(savedraft_blueprint, url_prefix='/api')
    app.register_blueprint(approvedenyreco_blueprint, url_prefix='/api')
    app.register_blueprint(smallapis_blueprint, url_prefix="/api")
    app.register_blueprint(expiredcampaigns_blueprint, url_prefix="/api")

load_dotenv()
env = os.environ.get("ENV")

login_manager = LoginManager()
jwt = JWTManager()


def create_app():
    app = Flask(__name__, root_path=str(Path(__file__).parent))
    app.config.from_object(app_setting)

    if env == "local":
        app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://" + os.environ['DB_USER'] + ":" + \
                                                os.environ['DB_PASS'] + "@" + os.environ['DB_INSTANCE_HOST'] + \
                                                ":5432/" + os.environ['DB_NAME']
    else:
        conn_string = f"Driver={db_driver};Server=tcp:{db_server},1433;Database={db_database};Uid={db_username};Pwd={db_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=560;"
        param = urllib.parse.quote_plus(conn_string)
        app.config["SQLALCHEMY_DATABASE_URI"] = f"mssql+pyodbc:///?odbc_connect={param}?connect_timeout=560"

    app.config['CACHE_TYPE'] = "SimpleCache"
    cache.init_app(app)
    app.config["SESSION_SQLALCHEMY"] = db
    db.init_app(app)
    Session(app)
    CORS(app)
    app.config.update({'SECRET_KEY': secrets.token_hex(64)})

    login_manager.session_protection = "strong"
    login_manager.init_app(app)
    jwt.init_app(app)
    app.logger.level = logging.DEBUG


    register_blueprints(app)  # Register all blueprints (appRoutes)

    return app


app = create_app()
app.app_context().push()

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/')
def index():
    print("deba-path")
    return "Home Page"

""" CREATE TABLE (RUN ONLY ONCE DURING FIRST SERVER START) """
# This drops existing tables and makes new one with static data inserted from db_script
# createdb()

with app.app_context():
    tables = inspect(db.engine).get_table_names()
    print("Fetching the table names... \n")
    print( "List of tables created: \n", tables, "\n")


# @app.before_first_request
def setup_schedulers():
    from apis.autoapprovalCronJob import my_cron_job
    from apis.orderqueue import execute_queue
    try:
        # QUEUE SCHEDULER
        queueScheduler = BackgroundScheduler(job_defaults={'max_instances': 1})
        queueScheduler.add_job(id="execute_queue",  func=execute_queue, trigger='interval', minutes=3)

        # AUTOAPPROVAL SCHEDULER
        autoApprovalScheduler = BackgroundScheduler(timezone=utc)

        # Schedule the job for 1:00 AM and for for 2:00 AM
        autoApprovalScheduler.add_job(id='my_cron_job_1', func=my_cron_job, trigger='cron', hour=1, minute=0)
        autoApprovalScheduler.add_job(id='my_cron_job_2', func=my_cron_job, trigger='cron', hour=2, minute=0)

        queueScheduler.start()
        autoApprovalScheduler.start()

    except Exception as e:
        print(f"error occured in Setting up CRON-JOB schedulers: {str(e)}")    

# for dev execution uncomment function here
""" Commenting the scheduler function because we are running it on aseperate pod in branch 'seperatePod'
This code will go to Develop which will accept all req and not ptocess queue. Seperate pods won't process
any req and will just implement queue  """
# setup_schedulers()

if __name__ == "__main__":
    print("\nStarting Backend Server at PORT: 5001 \n ")
    
    # for local execution uncomment function here
    """ Commenting the scheduler function because we are running it on aseperate pod in branch 'seperatePod'
    This code will go to Develop which will accept all req and not ptocess queue. Seperate pods won't process
    any req and will just implement queue  """
    # setup_schedulers()
    app.run(port=5001, debug=True)
    
    
