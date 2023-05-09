#!/usr/bin/env python
# coding: utf-8

import os
import ssl
import json
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta

def get_site_configuration(client):
    db = client['site_configurations']
    data_json = db.INTL_TINT_site_config.find()
    return pd.DataFrame(list(data_json))

def get_raw_nwc_data(client, from_date, to_date):
    db = client['network_window_controller']
    from_date = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    to_date = datetime.strptime(to_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    criteria = {"$and": [{"created_at": {"$gte": from_date, "$lte": to_date}}]}
    data_json = db.timeseries_data.find(criteria)
    df = pd.DataFrame(list(data_json))
    print("Number of rows of NWC data found in the DataFrame:", len(df))
    return df

def create_connection(host):
    MONGO_PKEY = 'mongodb-ca.pem'
    MONGO_PRIVATEKEY = 'mongodb-cert-key.pem'
    port_user = 27017
    print("Opening Connection...")
    return MongoClient(host, port=port_user, ssl=True, ssl_certfile=MONGO_PRIVATEKEY, ssl_ca_certs=MONGO_PKEY, ssl_cert_reqs=ssl.CERT_NONE, connect=True)

def check_building(client):
    try:
        site_configuration = get_site_configuration(client)[["_id", "buildingId"]]
        buildingId = site_configuration.iat[0, 1]
        print(f'The Building Id is {buildingId}')
    except:
        print(f'The zone configuration has not been pushed to site.')
    return buildingId

def write_to_file(datafile, buildingId, from_date):
    from_date_obj = datetime.strptime(from_date, "%Y-%m-%dT%H:%M:%S.%fZ")
    from_date_formatted = from_date_obj.strftime("%Y-%m-%d")
    file_name = f'{buildingId}_raw_nwc_data_{from_date_formatted}.csv'
    cwd = os.getcwd()
    print(f"Outputting Data to {cwd}\\{file_name}")
    datafile.to_csv(file_name, index=False)

if __name__ == '__main__':
    MONGO_HOST = input('Please enter Tailscale IP address of DB (eg: 100.73.214.6):')
    time_selection = input("Would you like to download data for: (1) the last 15 minutes OR (2) or last 4 hours OR (3) specify timestamps?")
    if time_selection == "3":
        from_date = input('Please enter properly formatted start date/time in UTC for WC Data (eg: 2022-05-24T05:30:54.000Z):')
        to_date = input('Please enter properly formatted end date/time in UTC for WC Data (eg: 2022-05-24T05:30:54.000Z):')
    else:
        delta = timedelta(minutes=-15) if time_selection == "1" else timedelta(hours=-4)
        from_date, to_date = (datetime.utcnow() + delta).isoformat()[:23] + 'Z', datetime.utcnow().isoformat()[:23] + 'Z'

    print(f"Pulling NWC data from between {from_date} and {to_date}")
    client = create_connection(MONGO_HOST)
    buildingId = check_building(client)
    raw_nwc_data = get_raw_nwc_data(client, from_date, to_date)
    write_to_file(raw_nwc_data, buildingId, from_date)




