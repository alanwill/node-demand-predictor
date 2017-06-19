# coding: utf-8
from __future__ import (absolute_import, division, print_function, unicode_literals)

import json
import logging
import boto3
import os
import sys
import csv
import time
from botocore.exceptions import ClientError

# Path to modules needed to package local lambda function for upload
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(currentdir, "./vendored"))

# Modules downloaded into the vendored directory

# Logging
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Initializing AWS services
s3 = boto3.client('s3')
ml = boto3.client('machinelearning')


def handler(event, context):
    log.debug("Received event {}".format(json.dumps(event)))

    # Read incoming event payload and extract bucket and object
    s3Bucket = event['Records'][0]['s3']['bucket']['name']
    s3Object = event['Records'][0]['s3']['object']['key']

    # Since the same bucket is being used for both the json and csv file
    # Check to make sure we're only acting on the json file
    if s3Object != 'sample.json':
        return

    convert_to_csv(s3Bucket, s3Object)
    return create_model(s3Bucket)



def create_model(s3_bucket):

    mlDatasource = ml.create_data_source_from_s3(
        DataSourceId='nodeDemandPredictionCsv' + time.time(),
        DataSourceName='Node Demand Prediction Source',
        DataSpec={
            'DataLocationS3': 's3://' + s3_bucket + '/nodeDemand.csv',
            'DataSchema': '{"version": "1.0","rowId": null,"rowWeight": null,"targetAttributeName": "nodes","dataFormat": "CSV","dataFileContainsHeader": true,"attributes": [{"attributeName": "job","attributeType": "CATEGORICAL"}, {"attributeName": "demand","attributeType": "NUMERIC"}, {"attributeName": "nodes","attributeType": "NUMERIC"}],"excludedAttributeNames": []}',
        },
        ComputeStatistics=True
    )

    mlModel = ml.create_ml_model(
        MLModelId='nodeDemandPrediction' + time.time(),
        MLModelName='Node Demand Prediction Model',
        MLModelType='REGRESSION',
        TrainingDataSourceId=mlDatasource['DataSourceId']
    )

    realtimeEndpoint = ml.create_realtime_endpoint(
        MLModelId=mlModel['MLModelId']
    )

    return mlModel['MLModelId']

def convert_to_csv(s3_bucket, s3_object):
    s3.download_file(s3_bucket, s3_object, '/tmp/nodeDemand.json')

    with open('/tmp/nodeDemand.json') as f:
        nodeDemandJson = json.load(f)

    nodeDemandCsv = csv.writer(open('/tmp/nodeDemand.csv', 'w'))
    nodeDemandCsv.writerow(["job", "demand", "nodes"])

    for i in nodeDemandJson['jobs']:
        nodeDemandCsv.writerow([i['name'], i['data'][0]['demand'], i['data'][0]['nodes']])
        for ii in i['data'][1:]:
            nodeDemandCsv.writerow(["", ii['demand'], ii['nodes']])

    s3.upload_file('/tmp/nodeDemand.csv', s3_bucket, 'nodeDemand.csv')

    return
