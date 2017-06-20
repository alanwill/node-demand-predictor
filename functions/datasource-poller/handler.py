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
    mlDatasourceId = event['datasourceId']

    datasourceStatus = ml.get_data_source(
        DataSourceId=mlDatasourceId
    )

    if datasourceStatus['Status'] == 'COMPLETED':
        print('Datasource ready')
        mlModelId = create_model(mlDatasourceId)
        schedule_datasource_poller(mlModelId)
        cleanup()
    else:
        return

def create_model(ml_datasource_id):

    mlModel = ml.create_ml_model(
        MLModelId='nodeDemandPrediction' + str(time.time()),
        MLModelName='Node Demand Prediction Model',
        MLModelType='REGRESSION',
        Parameters={
            'sgd.maxMLModelSizeInBytes': '104857600',
            'sgd.maxPasses': '10',
            'sgd.shuffleType': 'auto'
        },
        TrainingDataSourceId=ml_datasource_id
    )

    return mlModel['MLModelId']


def schedule_datasource_poller(model_id):

    cwevents.put_rule(
        Name='node-demand-predictor-modelpoll-1m',
        ScheduleExpression='rate(1 minute)',
        State='ENABLED',
        Description='Runs poller every 1 minute'
    )

    cwevents.put_targets(
        Rule='node-demand-predictor-modelpoll-1m',
        Targets=[
            {
                'Id': '1',
                'Arn': os.environ['LAMBDA_MODEL_POLLER_ARN'],
                'Input': json.dumps({"modelId": model_id})
            }
        ]
    )

    return


def cleanup():
    cwevents.remove_targets(
        Rule='node-demand-predictor-datasourcepoll-1m',
        Ids=[
            '1',
        ]
    )

    cwevents.delete_rule(
        Name='node-demand-predictor-datasourcepoll-1m'
    )

    return
