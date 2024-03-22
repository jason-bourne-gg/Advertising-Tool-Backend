# from models import Campaign
# from sqlalchemy import update
# from database import db
# import json

# try:
#     stmt = update(Campaign).where(Campaign.order_id == 583756636260352528).values(product_tracking_list= json.dumps({"fileName": "productlist.csv", "defaultSelected": True}))
#     # camp_obj = Campaign.query.filter_by (order_id = "583756636260352528")
#     # camp_obj.product_tracking_list = '{"fileName": "productlist.csv", "defaultSelected": True}'

#     db.session.execute(stmt)
#     db.session.commit()

#     print("commited changes in to db")

# except Exception as e:
#     print("error:", e )    