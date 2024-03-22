import pandas as pd
from datetime import datetime, timedelta,timezone
import itertools
from settings. config import db_database,db_driver,db_password,db_server,db_username,container_name, connection_string,advertiser_id,storage_account_name,account_access_key
import pyodbc
import logging as logger
from dotenv import load_dotenv
import os,io
from azure.storage.blob import BlobServiceClient
import re
from database import db
from sqlalchemy import text
import pyarrow.parquet as pq
import pyarrow as pa
import uuid
import calendar



load_dotenv()
env = os.environ.get("ENV")

def generate_request_id():
    unique_id = str(uuid.uuid4())
    # timestamp = str(int(time.time() * 1000))  # Multiply by 1000 to get milliseconds
    request_id = unique_id
    return request_id


def get_last_run_date(brand_id):
    sql_query = text(f"SELECT MAX(Last_updated_on) FROM de_brand_settings WHERE line_item_count > 0 AND brand_id = {brand_id}")
    try:
        result = db.session.execute(sql_query, {'brand_id': brand_id}).scalar()
        print("date" , result)
    except Exception as e:
        raise Exception("Error: " + str(e))
    return result


def read_files_from_azure_container(blob_prefix):
    container_name = "pulse"
    dfs = []
    print(blob_prefix)
    # Azure Blob Storage client
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(container_name)

    # Get a list of blobs in the container with the specified prefix
    blobs = container_client.list_blobs(name_starts_with=blob_prefix)
    print(blobs) 
    print(type(blobs))
    # Iterate over the blobs and read Parquet files
    # dfs = []
    for blob in blobs:
        if blob.size > 0 and  blob.name.endswith(".csv") or blob.name.endswith(".parquet"):
            blob_client = container_client.get_blob_client(blob)
            data = blob_client.download_blob().readall()
            try:
                buffer = io.BytesIO(data)
                df = pd.read_csv(buffer)
                # print(df.head())
                dfs.append(df)
            except Exception as e:
                print(f"Error reading file {blob.name}: {e}")

    # Concatenate the pandas DataFrames into a single pandas DataFrame
    df = pd.concat(dfs)
    # print(df.head())
    return df


def read_sql_table(table, brand_id):
    try :
        sql_query = text(f"SELECT * FROM {table} JOIN brand ON {table}.brand_id = brand.id WHERE brand_id = {brand_id} AND Last_updated_on = (SELECT MAX(Last_updated_on) FROM de_brand_settings WHERE line_item_count > 0 AND brand_id = {brand_id})")
        result = db.session.execute(sql_query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        print("TBALE 2 data")
        print(df.head())
        return df 
    
    except Exception as e:
        logger.error(f" Exception raised : {e}")
        print(f'error : {e}')
        raise e


def read_new_sql_table(table_name):
    try :
        query = text(f"SELECT * FROM {table_name}")
        result = db.session.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        print("Printing new table data")
        print(df.head())
        return df 
    
    except Exception as e:
        logger.error(f" Exception raised : {e}")
        print(f'error : {e}')
        raise e


''' This function calculates numbers of days for which new flights have to be initated and then initates new
    flights of specific period until the last flight which can be of smaller days depending on order end date
'''
def select_aud(brand,new_aud_num,rank_2,rank_3,low_vol_ranks,neg_aud):
    new_aud_dict ={}

    for key in new_aud_num:
        new_aud_list =[]
        if ((key in rank_2['Context'].unique()) & (key in rank_3['Context'].unique())):
            prob_rank_2 = rank_2[rank_2['Context']==key]
            prob_rank_2=prob_rank_2.sort_values(by='rank_median')

            prob_rank_3 = rank_3[rank_3['Context']==key]
            prob_rank_3=prob_rank_3.sort_values(by='rank_median')

            interval = 10
            slicer = interval
            count = (prob_rank_2.shape[0]/interval)+1

            while count*interval>=slicer:

                df_rank_2 = prob_rank_2[(prob_rank_2['rank_median']<=slicer) & (prob_rank_2['rank_mean']<=slicer)&(prob_rank_2['rank_min']<=slicer)]
                df_rank_3 = prob_rank_3[(prob_rank_3['rank_median']<=slicer) & (prob_rank_3['rank_mean']<=slicer)&(prob_rank_3['rank_min']<=slicer)]

                aud_rank_2 = list(df_rank_2['Audience'])
                aud_rank_3 = list(df_rank_3['Audience'])

                for aud in aud_rank_2:
                    if((len(new_aud_list)<new_aud_num[key])&(aud in aud_rank_3) & (aud not in new_aud_list) & ('productcategory' not in aud) & ('context' not in aud) & (aud not in neg_aud)):
                        new_aud_list.append(aud)

                slicer = slicer + interval

                if len(new_aud_list)==new_aud_num[key]:
                    break
                    
        elif key in low_vol_ranks['Context'].unique():
            low_vol_ranks_context = low_vol_ranks[low_vol_ranks['Context']==key]
            low_vol_ranks_context=low_vol_ranks_context.sort_values(by='final_rank')
            low_vol_ranks_context = low_vol_ranks_context[~low_vol_ranks_context['Audience'].str.contains('productcategory')].reset_index(drop=True)
            low_vol_ranks_context = low_vol_ranks_context[~low_vol_ranks_context['Audience'].str.contains('context')].reset_index(drop=True)
            low_vol_ranks_context = low_vol_ranks_context[~low_vol_ranks_context['Audience'].isin(neg_aud) ].reset_index(drop=True)
            
            
            count = new_aud_num[key]
            new_aud_list = list(low_vol_ranks_context['Audience'][:int(count)])

            
        else:
            low_vol_ranks__ =  low_vol_ranks[low_vol_ranks['Context']==low_vol_ranks['Context'][0]]
            low_vol_ranks__ = low_vol_ranks__.sort_values(by='final_rank')
            low_vol_ranks__ = low_vol_ranks__[~low_vol_ranks__['Audience'].str.contains('productcategory')].reset_index(drop=True)
            low_vol_ranks__ = low_vol_ranks__[~low_vol_ranks__['Audience'].isin(neg_aud)].reset_index(drop=True)
            low_vol_ranks__ = low_vol_ranks__[~low_vol_ranks__['Audience'].str.contains('context')].reset_index(drop=True)
            
            count = new_aud_num[key]
            new_aud_list = list(low_vol_ranks__['Audience'][:int(count)])

        new_aud_dict[key]=new_aud_list
        print(len(new_aud_dict[key]))                 
        
    output_df = pd.DataFrame(list(new_aud_dict.items()), columns=['Context', 'Audience'])
    output_df=output_df.explode('Audience').reset_index(drop=True)
    output_df["Brand"] = brand
    return output_df


def add_flights(order_end_date,order_start_date,min_thresh,Total_Budget):
    flight=[]
    last_flight = order_start_date

    budget_day = Total_Budget/int((order_end_date - order_start_date).days)
    while(len(flight)<2):
        num_days_in_month=calendar.monthrange(last_flight.year, last_flight.month)[1]
        if(last_flight.day>15):
            new_flight = {}
            flight_period= num_days_in_month-last_flight.day+1  #both star asnd end date are accounted
#             print(num_days_in_month)
#             print(last_flight)
#             print(last_flight+timedelta(flight_period))
            if(flight_period)>min_thresh:
                new_flight['startDateTime'] = pd.to_datetime(last_flight+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['endDateTime'] = (last_flight+timedelta(flight_period)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['amount']=round(budget_day*flight_period)
            else:
                flight_period = flight_period+15
                new_flight['startDateTime'] = pd.to_datetime(last_flight+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['endDateTime'] = (last_flight+timedelta(flight_period)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['amount']=round(budget_day*flight_period)


            last_flight= last_flight+timedelta(flight_period)

            if(new_flight['amount']<1):
                new_flight['amount']=1
            flight.append(new_flight)  

        else :
            new_flight = {}
            flight_period= 15-last_flight.day+1   #both star and end date are accounted
            if(flight_period)>min_thresh:
                new_flight['startDateTime'] = pd.to_datetime(last_flight+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['endDateTime'] = (last_flight+timedelta(flight_period)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['amount']=round(budget_day*flight_period)
            else:
                flight_period = num_days_in_month-last_flight.day+1  
                new_flight['startDateTime'] = pd.to_datetime(last_flight+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['endDateTime'] = (last_flight+timedelta(flight_period)).strftime('%Y-%m-%d %X')+" UTC"
                new_flight['amount']=round(budget_day*flight_period)


            last_flight= last_flight+timedelta(flight_period)

            if(new_flight['amount']<1):
                new_flight['amount']=1
            flight.append(new_flight)  
        #print(flight_period)
    new_flight = {}
    flight_period =  int((order_end_date - last_flight).days)
    new_flight['startDateTime'] = pd.to_datetime(last_flight+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
    new_flight['endDateTime'] = (last_flight+timedelta(flight_period)).strftime('%Y-%m-%d %X')+" UTC"
    new_flight['amount']=round(budget_day*flight_period)
    if(new_flight['amount']<1):
        new_flight['amount']=1
    flight.append(new_flight) 
    
    #one additional flight on 1 dollar    
    new_flight = {}
    new_flight['startDateTime'] = pd.to_datetime(pd.to_datetime(flight[len(flight)-1]['endDateTime'])+timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
    new_flight['endDateTime'] = (pd.to_datetime(new_flight['startDateTime'])+timedelta(15)-timedelta(0,1)).strftime('%Y-%m-%d %X')+" UTC"
    new_flight['amount']= 1
    flight.append(new_flight) 
    
    return flight
    


#operator between groups
def between_group(x):
    flag =0
    op = []
    for y in x:
        flag= flag+1
        if(y=='A' or y=='O' ):
            start = flag

            if(x[start-1:start+2]=='AND'):
                op.append('AND')
            if(x[start-1:start+1]=='OR'):
                op.append('OR')
            
    return op

# get a list of groups present in an audience 
def list_of_aud_groups(x):
    #for x in data['Audience_include_logic']:
    flag =0
    aud = []
    for y in x:
        flag= flag+1
        if(y=='(' or y=='[' ):
            start = flag
        if(y==')' or y==']'):
            aud.append(x[start-1:flag])
            
    return aud

#with in group operator
def with_in_group(x):
    intra = []
    for y in x:
        if(y=='('):
            intra.append('ANY')
        if(y=='['):
            intra.append('ALL')
    return intra

#list of audiences in a group
def get_subgroups(x):
    aud_list = []
    for i in x:
        aud_list.append(i.split(';'))
    
    return aud_list

#basic cleaning of of audience
def clean_aud(aud):
    to_replace = ['(',')','[',']','NOT']
    for i in to_replace:
        aud=aud.replace(i,'')
        
    return aud.strip()
    
#mapping for linetype
line_type = {
    "SD" : ["STANDARD_DISPLAY","standardDisplayTargeting"],
    "AAP" : ["AAP_MOBILE_APP","aapMobileAppTargeting"],
    "AMD" : ["AMAZON_MOBILE_DISPLAY","amazonMobileDisplayTargeting"],
    "VIDEO" : ["VIDEO","videoTargeting"]
}

device_type = {
    "DTMB" : "DESKTOP_AND_MOBILE","MOBILE" : "MOBILE","DESKTOP" : "DESKTOP",
    "CONNECTED_TV" : "CONNECTED_TV",
    "APP" : [ "IPHONE", "IPAD", "ANDROID", "KINDLE_FIRE", "KINDLE_FIRE_HD" ],
    "ALL" : [ "MOBILE", "DESKTOP", "CONNECTED_TV" ]
}

supply_source_list = {
    "SD" : {"3P" : ["AJA","Ad Generation","Equativ","Fluct","Google AdX (Authorized Buyers)","Improve Digital","Index","Kargo","Magnite DV+","Media.net","OneTag", "OpenX","PubMatic","Smartadserver","Sovrn","Stroer","Taboola","Teads","Triplelift","Verizon Media Exchange","Xandr","YieldOne","Yieldlab"],"AZPS" :["Amazon Publisher Services"] ,"AZOO" : ["Amazon"],"IMDB" :["IMDb"] },
    "AMD": {"3P" :[] ,"AZPS" :[] ,"AZOO" :["Amazon mobile web","Amazon shopping app"] ,"IMDB" : ["IMDb mobile web"]},
    "AAP" : {"3P" : ["AJA","Ad Generation","AdColony","Google AdX (Authorized Buyers)","Improve Digital","InMobi","Magnite DV+","MoPub","OneTag","OpenX","PubMatic","Smaato","Smartadserver","Teads","Verizon Media Exchange","YieldOne","Yieldlab"],"AZPS" :["Amazon Publisher Services" ],"AZOO" : [],"IMDB" : ["IMDb mobile app"]}
}

def get_payload(UI_input_payload):
    viewability =  int(re.findall(r'\d+', UI_input_payload['suggestion']['viewability'])[0])
    final_view =''
    if viewability >= 80:
        final_view='ALLOW_ALL'
    elif viewability >= 70:
        final_view='VIEWABILITY_TIER_GT_70'
    elif viewability >= 60:
        final_view='VIEWABILITY_TIER_GT_60'
    elif viewability>= 50:
        final_view='VIEWABILITY_TIER_GT_50'
    elif viewability>= 40:
        final_view='VIEWABILITY_TIER_GT_40'
    else:
        final_view='VIEWABILITY_TIER_LT_40'
        

    #define flight
    # flight_period=13
    ##read inputs from table -2 
    # if env == "local":
    #     table_2 = pd.read_csv("src/apis/createCampaignAPIs/getPayloadFunction/table_2_params_copy.csv")
    # else:
    brand_id = UI_input_payload["brand"]["id"]
    table_name = "de_brand_settings"
    table_2 = read_sql_table(table_name, brand_id)
    # print(table_2.head(5))
    
    if table_2.empty : 
        return ({"error" : 'Cannot read table 2'})

    ##brand name 
    brand = UI_input_payload["brand"]["name"].lower()
    print(brand)
    
    category = read_new_sql_table("de_dsp_product_final")
    supply_source = read_new_sql_table("de_supply_source")

    

    
    #-------------------------select audience-----------------------#
    ##context and bids from UI
    context =[]
    bid = {}
    for cntxt_bid in UI_input_payload['suggestion']['context: bid']:
        first_pair = next(iter(cntxt_bid.items()))
        context.append(first_pair[0])
        bid[first_pair[0]] = first_pair[1]
    
    # print("contexts : " , context)
    ##number of audiences for each context
    new_aud_num={}

    # table_2 = table_2[table_2["brand_name"]==brand.upper()]
    print("Printing table 2 near brand issue" , table_2.head())

    for idx,raw in table_2.iterrows():
        if(raw["context"] in context):
            new_aud_num[raw["context"]]=raw["line_item_count"] 
    # new_aud_num[i]=line_item_count/len(context)

    print("new_aud_num : " , new_aud_num)
    
    ##import model outputs
    # if env == "local":
    #     rank_2 = pd.read_excel("src/apis/createCampaignAPIs/getPayloadFunction/recommendation_output.xlsx",sheet_name="probability_rank_2",usecols=["brand","combination","audience","rank_median","rank_mean","rank_min"])
    # else:
    # Format the date as "YYYY_MM_DD"
    date_from_query = get_last_run_date(UI_input_payload['brand']['id'])
    date_obj = datetime.strptime(str(date_from_query), "%Y-%m-%d")
    formatted_date = date_obj.strftime("%Y_%m_%d")
    date = str(formatted_date)
    print(date)
    # date = "2023_07_12"
    blob_name = f'data/amc/ds_models/{date}/{brand}/OUTPUT/recommendation_output_probability_rank_2.csv'
    rank_2 = read_files_from_azure_container(blob_name)
    print("probablity_rank2 data: ")
    print(rank_2.head(5))

    rank_2 = rank_2[rank_2["brand"]==brand]
    rank_2 =rank_2.rename(columns = {"combination":"Context", "audience":"Audience"})

    # if env == "local":
    #     rank_3 = pd.read_excel("src/apis/createCampaignAPIs/getPayloadFunction/recommendation_output.xlsx",sheet_name="probability_rank_3",usecols=["brand","combination","audience","rank_median","rank_mean","rank_min"])
    # else:
    blob_name = f'data/amc/ds_models/{date}/{brand}/OUTPUT/recommendation_output_probability_rank_3.csv'
    rank_3 = read_files_from_azure_container(blob_name)
    print("probablity_rank3 data: ")
    print(rank_3.head(5))

    rank_3 = rank_3[rank_3["brand"]==brand]
    rank_3 =rank_3.rename(columns = {"combination":"Context" , "audience":"Audience"})

    # if env == "local":
    #     low_vol_ranks = pd.read_excel("src/apis/createCampaignAPIs/getPayloadFunction/recommendation_output.xlsx",sheet_name="low_volume_recommendations",usecols=["brand","context","Audience","final_rank"])
    # else:
    blob_name = f'data/amc/ds_models/{date}/{brand}/OUTPUT/recommendation_output_low_volume_recommendations'
    low_vol_ranks = read_files_from_azure_container(blob_name)
    print("low vol recos: ")
    print(low_vol_ranks.head(5))

    low_vol_ranks = low_vol_ranks[low_vol_ranks["brand"]==brand]
    low_vol_ranks =low_vol_ranks.rename(columns = {"combination":"Context", "rank": "final_rank", "audience":"Audience"})
    low_vol_ranks


    audience_table = read_new_sql_table("de_audience")
    neg_aud = ['(' + aud + ")" for aud in audience_table[audience_table["category"]=="Negative Targeting"]["audienceId"]]
    neg_aud = neg_aud + ['[' + aud + "]" for aud in audience_table[audience_table["category"]=="Negative Targeting"]["audienceId"]]
    print("negative_aud :" ,neg_aud )

    # if rank_2.empty | rank_3.empty:

    #     selected_audience = low_vol_select_aud(new_aud_num,low_vol_ranks,brand)
    # else : 
    #     selected_audience = select_aud(new_aud_num,rank_2,rank_3,brand)
    # #do not take product category audience     
    # selected_audience
    selected_audience = select_aud(brand,new_aud_num,rank_2,rank_3,low_vol_ranks,neg_aud)
    print("selected_audience : ", selected_audience.head())

    ##user input for audience
    additional_aud=[]

    if len(UI_input_payload['audienceIds'][0]['data'])!=0:
     #below for loop will be in this
        for user_input in UI_input_payload["audienceIds"]:
            aud =""
            for group in user_input["data"]:
                formatted_group = ""
                intraOperator = group["intraOperator"]
                interOperator = group["interOperator"]
                audience_ids = [(i["audience_id"],i["include"]) for i in group["audience_ids"]]

                for aud_info in audience_ids:
                    if aud_info[1]==False:
                        formatted_group = formatted_group+ ";"+" NOT " + aud_info[0]
                    else:
                        formatted_group = formatted_group +";" +" "+ aud_info[0]

                if formatted_group[0]==";":
                    formatted_group=formatted_group[1:]
                formatted_group = formatted_group.strip()

                if intraOperator == "or":
                    formatted_group = "(" + formatted_group + ")"
                else :
                    formatted_group = "[" + formatted_group + "]"

                aud = aud+formatted_group+" " +interOperator.upper()+ " "

            aud = aud.strip()
            if interOperator=="or":
                aud = aud[:-2]
            else:
                aud = aud[:-3]
            aud = aud.strip()

            additional_aud.append(aud)
    print("additional_aud :", additional_aud)
    count=0
    for aud in additional_aud:
        if aud not in list(selected_audience["Audience"]):
            count = count+1
    
    print("count :", count )
    additional_aud_df = pd.DataFrame()
    if(len(additional_aud)>0):
        combinations = list(itertools.product(context, additional_aud))
        additional_aud_df = pd.DataFrame(combinations, columns=["Context", "Audience"])

    additional_aud_df
    print("additional_aud_df:", additional_aud_df)

    audience=pd.DataFrame()
    for context in selected_audience["Context"].unique():
        aud_context = selected_audience[selected_audience["Context"]==context]
        if count > 0:
            aud_context = aud_context[:-count]
            print("aud_context in IF:" , aud_context)
        else:
            aud_context = aud_context[:]
        audience = pd.concat([audience,aud_context],axis=0)
        # print(context)

    print("Audience before concat : ", audience)
    if count > 0:
        audience = pd.concat([audience,additional_aud_df],axis=0).reset_index(drop=True)       
    audience["Brand"]=brand
    print("audience_data = ", audience)
    
    #count of lineitems to be made
    line_item_count = audience.shape[0]
    print("line_item_count = " , line_item_count)
    
    
    #-----------------------flight-------------------------------#
    min_thresh = 7
    order_start_date = pd.to_datetime(UI_input_payload["startDate"])
    order_end_date = pd.to_datetime(UI_input_payload["endDate"])
    Total_Budget = float(UI_input_payload["totalBudget"])
    flights  = add_flights(order_end_date,order_start_date,min_thresh,Total_Budget)
    #------------------------lineitems----------------------#
    
    audience["supply_source"] = audience["Context"].apply(lambda x: x.split("|")[2].strip())
    audience["device_type"] = audience["Context"].apply(lambda x: x.split("|")[1].strip())
    audience["line_type"] = audience["Context"].apply(lambda x: x.split("|")[0].strip())
    audience["list_groups"] = audience["Audience"].apply(lambda x : list_of_aud_groups(x))

    audience["between_group_op"] = audience["Audience"].apply(lambda x : between_group(x))

    audience["between_group_op"].apply(lambda x : x.append("OR"))


    audience["with_in_group_op"] = audience["Audience"].apply(lambda x : with_in_group(x))
    audience["subgroups"] = audience["list_groups"].apply(lambda x : get_subgroups(x))

    """Note: divide budget equally in all the lineitems"""
    no_days =int((order_end_date - order_start_date).days)

    budgetCaps = round((Total_Budget/no_days)/line_item_count)
    order_budgetCap =round((Total_Budget/(no_days))*(1+0.3))

    if(order_budgetCap<=1):
        order_budgetCap=1

    if(budgetCaps<=1):
        budgetCaps=1
    
    ##creating a list of lineitem details
    lineitems=[]

    for idx,row in audience.iterrows():
        new_lineitem = {}

        #line_type
        new_lineitem["lineItemType"] = line_type[row["line_type"]][0]
        line_type_targetting = line_type[row["line_type"]][1]

        #line_name 
        date= pd.to_datetime('today').strftime("%d-%m-%Y")
        new_lineitem['name']=f'{brand} | {row["Context"]} | {date} | {idx}'

        #this will be from UI (user input)    
        new_lineitem["startDateTime"]= flights[0]["startDateTime"]
        new_lineitem["endDateTime"]= flights[len(flights)-1]["endDateTime"]

        #ask agam to get codes for current brands lineitems
        new_lineitem['lineItemClassification']= {}
        new_lineitem['lineItemClassification']["productCategories"]=list(set(category[category['brand']==row['Brand']]['product_id']))
        
        #UI input
        new_lineitem["frequencyCap"]= {
                "type": "CUSTOM",
                "maxImpressions": UI_input_payload["suggestion"]["frequency_cap_amount"],
                "timeUnitCount": UI_input_payload["suggestion"]["frequency_cap_days"],
                "timeUnit": "DAYS"
            }
        ##SQL table
        new_lineitem["budget"]= {
                "budgetCaps": [
                    {
                        "amount": budgetCaps,
                        "recurrenceTimePeriod": "DAILY"
                    }
                ],
                "pacing": {
                    "deliveryProfile": "EVENLY",
                    "catchUpBoost": "NONE"
                }
            }
        ##same as frequency 
        new_lineitem["bidding"]= {
                "baseSupplyBid": bid[row["Context"]],

            }
        ##hardcoded
        new_lineitem["optimization"]= {
                "budgetOptimization": True
            }
        new_lineitem["creativeOptions"]= {
            "creativeRotationType": "RANDOM"
            }
        new_lineitem["targeting"]={
                f"{line_type_targetting}": {
                    #hardcoded
                    "userLocationTargeting": "US",
                    #input from blender
                    "segmentTargeting": {

                    },
                    #UI
                    "amazonViewabilityTargeting": {
                        "viewabilityTier": final_view,
                        "includeUnmeasurableImpressions": False
                    },


                    ## we don"t have mapping right now so hardcoded 
                    "supplyTargeting": {
                        "supplySourceTargeting": {
#                             "supplySources": 
                        }
                    },
                    ##UI but we need to confirm and also get mappings           !!!!!!!!will be added in second run!!!!
                    "geoLocationTargeting": {
                        "inclusions": [

                        ],
                        "exclusions": [

                        ]
                    },


                    # "deviceTypeTargeting": "DESKTOP_AND_MOBILE",


                }
            }
        #device type
        if(row["line_type"]!="AMD"):
            new_lineitem["targeting"][line_type_targetting]["deviceTypeTargeting"]=device_type[row["device_type"]]


        #contextual
        if(row['line_type']!='AAP'):
            new_lineitem["targeting"][line_type_targetting]["contextualTargeting"]=False
            if len(row["with_in_group_op"])==0:
                new_lineitem["targeting"][line_type_targetting]["contextualTargeting"]=True


        #audience or Segment Targetting
        aud_targetting=[]
        count=0
        for segment in row["subgroups"]:
            seg_dict={}
            segments=[]
            for segment_id in segment:
                aud={}

                if "NOT" in segment_id:
                    aud["isNot"]=True
                aud["segmentId"] = clean_aud(segment_id)
                segments.append(aud)
            seg_dict["segments"]=segments
            seg_dict["intraOperator"]=row["between_group_op"][count]     
            seg_dict["interOperator"]=row["with_in_group_op"][count]

            aud_targetting.append(seg_dict)
            count = count+1

        new_lineitem["targeting"][line_type_targetting]["segmentTargeting"]["segmentGroups"]=aud_targetting
        

        #supply source
        supply_source_code=[]
        for ss in row["supply_source"].split():
            ss = ss.strip()
            filter_ss = supply_source[(supply_source['line_type']==row['line_type']) & (supply_source['supply_source']==ss)]
            filter_ss = filter_ss[ filter_ss['category'].isin(supply_source_list[row['line_type']][ss])]
            supply_source_code = supply_source_code + list(filter_ss['codes'])
            
        new_lineitem["targeting"][line_type_targetting]["supplyTargeting"]["supplySourceTargeting"]["supplySources"]=supply_source_code

        #append to list
        lineitems.append(new_lineitem)

        if(idx==0):
            print(new_lineitem)    

    #---------------------Order------------------#
    
    ##creating an order and appending the above line item list to this orders
    new_order={
        "requestId":generate_request_id(),
        ##SQL table
        "orderPONumber" : UI_input_payload["orderPONumber"],
        "totalLineItems":line_item_count,
        #hardcoded
        "advertiserId" : "5797658410201",
        ##UI
        "name":  UI_input_payload["campaignName"],
        ##hardcode other than flights
        "budget":{
                "budgetCaps":[{
                    "recurrenceTimePeriod": "DAILY",
                    "amount": order_budgetCap}],
                "flights":flights
             
        },

        "optimization": {
            #hardcoded
            "productLocation": "SOLD_ON_AMAZON",
            #UI
            "goal": UI_input_payload["goal"]["goal"],
            "goalKpi": UI_input_payload["goalKPI"],
            #hardcoded
            # "autoOptimizations": [
            #     "BUDGET","BID"
            # ],
            "biddingStrategy": "SPEND_BUDGET_IN_FULL"
        },
        ##at order level hardcoded
        "frequencyCap": {
            "type": "UNCAPPED"
        },

    }
    if((UI_input_payload['goalKPI'].lower()!= 'other') & (UI_input_payload['goalKPI'].lower()!= 'none')):
        new_order['optimization']['autoOptimizations']=["BUDGET",'BID']

    new_order["lineitems"] = lineitems
    new_order["domainNames"]=UI_input_payload["domainNames"]
    new_order["product_tracking_list"]=UI_input_payload["product_tracking_list"]
    
    return (new_order)





