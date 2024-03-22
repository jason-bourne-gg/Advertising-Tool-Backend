"""
This class contains all the util functions which loads different config files.

"""
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()


# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def load_configs():
    config_file_path = os.path.dirname(__file__) + "/../resources/"+os.environ["ENV"]+".config.json"
    configs = dict()
    if config_file_path:
        if os.path.exists(config_file_path):
            with open(config_file_path, 'r') as config_file:
                configs = json.load(config_file)
        else:
            logger.error("Config path doesn't exists")
    else:
        logger.error("Missing CONFIG_FILE_LOCATION argument.")
    print(configs)
    return configs


# Loading Configs
logger.info("Configs Loading")



amc_configs = load_configs()
logger.debug(amc_configs)
env = os.environ.get("ENV")

def getENVValue(var):

    env_var_val = os.environ.get(var)
    return env_var_val

app_setting = amc_configs["APP_SETTING"]
redirect_uri = getENVValue(amc_configs["redirect_uri"])
okta_org_url = getENVValue(amc_configs["OKTA_SETTINGS"]["ORG_URL"])


if env == "local" or env=="dev":
    okta_client_id = getENVValue(amc_configs["OKTA_SETTINGS"]["CLIENT_ID"])
    okta_client_secret = getENVValue(amc_configs["OKTA_SETTINGS"]["CLIENT_SECRET"])

if env == "prod":
    okta_client_id = getENVValue(amc_configs["OKTA_SETTINGS"]["CLIENT_ID"])
    okta_client_secret = getENVValue(amc_configs["OKTA_SETTINGS"]["CLIENT_SECRET"])

okta_redirect_uri = getENVValue(amc_configs["OKTA_SETTINGS"]["OKTA_REDIRECT_URI"])
reckitt_okta_api_token = getENVValue(amc_configs["OKTA_SETTINGS"]["RECKITT_OKTA_API_TOKEN"])

storage_account_name = getENVValue(amc_configs["AZURE_SETTINGS"]["AZURE_ACC_NAME"])
account_access_key = getENVValue(amc_configs["AZURE_SETTINGS"]["AZURE_PRIMARY_KEY"])
container_name = getENVValue(amc_configs["AZURE_SETTINGS"]["AZURE_CONTAINER"])
sas_token = getENVValue(amc_configs["AZURE_SETTINGS"]["AZURE_ACCOUNT_SAS"])
connection_string = f'DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={account_access_key};EndpointSuffix=core.windows.net' 

db_server = getENVValue(amc_configs["AZURE_DB_SETTINGS"]["SERVER"])
db_database = getENVValue(amc_configs["AZURE_DB_SETTINGS"]["DATABASE"])
db_username = getENVValue(amc_configs["AZURE_DB_SETTINGS"]["USERNAME"])
db_password = getENVValue(amc_configs["AZURE_DB_SETTINGS"]["PASSWORD"])
db_driver = getENVValue(amc_configs["AZURE_DB_SETTINGS"]["DRIVER"])
db_connection_string = f"Driver={db_driver};Server={db_server},1433;Database={db_database};Uid={db_username};Pwd={db_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=300;"

refresh_token = getENVValue(amc_configs["AMAZON_DSP_SETTINGS"]["REFRESH_TOKEN"])
client_id = getENVValue(amc_configs["AMAZON_DSP_SETTINGS"]["CLIENT_ID"])
client_secret = getENVValue(amc_configs["AMAZON_DSP_SETTINGS"]["CLIENT_SECRET"])
profile_id = getENVValue(amc_configs["AMAZON_DSP_SETTINGS"]["PROFILE_ID"])
advertiser_id = getENVValue(amc_configs["AMAZON_DSP_SETTINGS"]["ADVERTISER_ID"])


# print("\nPrinting env variables: \n")
# print("storage_account_name:", storage_account_name)
# print("account_access_key:", account_access_key)
# print("container_name:", container_name)
# print("sas_token:", sas_token)
# print("connection_string:", connection_string)
# print("db_server:", db_server)
# print("db_database:", db_database)
# print("db_username:", db_username)
# print("db_password:", db_password)
# print("db_driver:", db_driver)
# print("refresh_token:", refresh_token)
# print("client_id:", client_id)
# print("client_secret:", client_secret)
# print("profile_id:", profile_id)
# print("advertiser_id:", advertiser_id)
# print("reckitt_okta_api_token:", reckitt_okta_api_token)


# refresh_token = 'Atzr|IwEBIA_xKM5nxz7_fTLj97VcZC_Rys7atwKdnbHMkeWWSg2r1qyTcG9ni2x0PUX-JVtNuDoENIwWPwduXtQvxTt7fJr0x65aqScd3JjLA_2jkiHccMRAHESQ9dIa0SYmMOwrhV7CazdF17eALlKJM8CxJUSFPMpUpJdNmudutg5oKl95u6imvqS76TLHotMjeFvNNU8uTUmH7j2C69xpnyZgdp3tjwG6ef18sdR5IVVzlO3ohoIUtH1nMvHb61GYAQHLp9zB1ugsMZhhz1SHeuH_cpGPaM4_oA0Meq5x1Pcg_YrYpC74kGsBk74Ze2mvanGVMMYTleF0jccOpfuDLzdYXaYD-wJGB16GNGisM0Fa4bsOiZXI9z-V-GbI9_FOerdKBHi8DI52E8VXe-Ilf8DrNwhLAFSlCBLXDv-HN7_XZWATnx5j0hfPAVIkHeBTZFLc-sGzuQKhj4H3cZR-6hBpFQ39'
# client_id = 'amzn1.application-oa2-client.7dd43a9855b74bf69ffa42199fa81399'
# client_secret = '11dccfe1169dba8d7e21aeeb7248654b9f0c7558361dbd761a6553274ad8ac47'
# profile_id="475484054892114"
# advertiser_id="5797658410201"

# shared_client_secret = getENVValue(amc_configs["PLACEORDER_API_AUTH_SETTINGS"]["SHARED_CLIENT_SECRET"])

# tenant_id = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["TENET_ID"])
# cc_api_client_id = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["CC_API_CLIENT_ID"])
# cc_api_client_secret = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["CC_API_CLIENT_SECRET"])
# subscription_id = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["SUBSCRIPTION_ID"])
# resource_group = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["RESOURCE_GROUP"])
# data_factory_name = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["DATA_FACTORY_NAME"])
# pipeline_name = getENVValue(amc_configs["CREATECAMPAIGN_API_SETTINGS"]["PIPELINE_NAME"])s

logger.info("Configs Loaded")




