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


def handler(event, context):
    log.debug("Received event {}".format(json.dumps(event)))

    # Read incoming event payload and extract DataSourceId
    mlModelId = event['modelId']

    modelStatus = ml.get_ml_model(
        MLModelId=mlModelId
    )

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