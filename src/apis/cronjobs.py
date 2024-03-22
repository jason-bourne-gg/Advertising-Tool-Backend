from flask import Flask,Blueprint,Response
import schedule
import time
from datetime import datetime, timezone
from models import  Campaign
from database import db
import logging
from flask_login import login_required


def update_campaign_status():
    today = datetime.now(timezone.utc).date()

    running_campaigns = Campaign.query.filter(Campaign.start_time >= today and Campaign.status == 'READY TO DELIVER').all()
    expired_campaigns = Campaign.query.filter(Campaign.end_time <= today and Campaign.status == 'RUNNING').all()

    for campaign in running_campaigns:
        campaign.status = 'RUNNING'

    for campaign in expired_campaigns:
        campaign.status = 'EXPIRED'

    db.session.commit()
    print("Campaign status updated successfully.")

# Schedule the cron job to run daily at 1:00 AM UTC
schedule.every().day.at("01:00").do(update_campaign_status)

while True:
    schedule.run_pending()
    time.sleep(1)