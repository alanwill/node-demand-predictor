# node-demand-predictor

## Overview

This app when passed a specific json dataset containing training data will convert said file to csv before using it to train a linear regression model using AWS Machine Learning. It will ultimately return an HTTP endpoint to be used for predicting node counts given a particular demand value.

The focus when building this app was around usability, function, security and autonomy. 

## Arch Diagram

<p align="center"><img src="assets/node-demand-predictor.jpg" alt="Node Demand Predictor Arch Diagram"></p>

## Installation
This app is built with Python running across a few Lambda functions. The deployment is encapsulated with CloudFormation and packaged with AWS SAM.  

## Obtaining Predictions
There's a couple ways to obtain a prediction:

1. From the Management Console navigate to the ML page and run the predictions from within the Model.
2. Use the AWS CLI `aws machinelearning predict`

## Todo
* Build API Gateway to ease accessibility of the tool 
* Hook up SNS to notify caller that prediction endpoint is ready for calling
* Orchestrate the existing Pollers with Step Functions to simplify and reduce some of the existing built in complexity