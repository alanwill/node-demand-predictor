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
cwevents = boto3.client('events')


# This lambda function polls the ML service's API every minute to check if the model is complete. Once it is,
# it creates the prediction endpoint the removes the scheduler.

def handler(event, context):
    log.debug("Received event {}".format(json.dumps(event)))

    # Read incoming event payload and extract DataSourceId
    mlModelId = event['modelId']

    modelStatus = ml.get_ml_model(
        MLModelId=mlModelId
    )

    # Check if the model is ready before moving on to create the prediction endpoint.
    if modelStatus['Status'] == 'COMPLETED':
        print('Model ready')
        create_realtime_endpoint(mlModelId)
        cleanup()
    else:
        return


def create_realtime_endpoint(ml_model_id):

    realtimeEndpoint = ml.create_realtime_endpoint(
        MLModelId=ml_model_id
    )

    return realtimeEndpoint['MLModelId']


# In order to avoid this Lambda function from running in perpetuity, remove the schedule

def cleanup():
    cwevents.remove_targets(
        Rule='node-demand-predictor-modelpoll-1m',
        Ids=[
            '1',
        ]
    )

    cwevents.delete_rule(
        Name='node-demand-predictor-modelpoll-1m'
    )

    return