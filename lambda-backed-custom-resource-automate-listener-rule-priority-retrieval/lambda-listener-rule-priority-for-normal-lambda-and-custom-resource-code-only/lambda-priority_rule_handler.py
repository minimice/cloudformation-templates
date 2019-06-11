### Created by Lim Chooi Guan AWS Certified SA ###
### Lambda fuction (see lambda_handler) which returns a listener rule priority for the a new/existing service ###
### Lamba function (see handler) which returns a listener rule priority for the a new/existing service, used for your custom backed lambda resource ### 
### Repository at http://github.com/minimice ###

#  curl -X POST -H "Content-Type: application/json" -d '{"listener_arn": "arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-dev/12345/6789","service_name": "lcg-fakeservice.lcg.com"}' https://fake12345.execute-api.eu-west-1.amazonaws.com/default/myALBHander

import boto3
import json
import time
from botocore.vendored import requests

def handler(event, context):

    # Sample request returned in the event object
    # {
    #     "RequestType": "Create",
    #     "ServiceToken": "FakeServiceToken",
    #     "ResponseURL": "https://fakeurlToCloudformation",
    #     "StackId": "arn:aws:cloudformation:eu-west-1:FakeAccount123:stack/fake/SomeId",
    #     "RequestId": "fake-requestId",
    #     "LogicalResourceId": "FakeInfo",
    #     "ResourceType": "Custom::FakeInfo",
    #     "ResourceProperties": {
    #         "listener_arn": "arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-dev/1234/5678",
    #         "service_name": "lcg-fakeservice.lcg.com"
    #     }
    # }
    # Format of this request is defined at https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-requests.html
    
    # Validation of RequestType and ResourceProperties
    if 'RequestType' not in event or 'ResourceProperties' not in event:
        return send_response(event, context, "FAILED", {"Message": "Unexpected event received from CloudFormation"})

    # Check request type
    request_type = event['RequestType']

    # Return success immediately if deleting
    if event['RequestType'] == 'Delete':
        return send_response(event, context, "SUCCESS", {"Message": "Resource deletion successful!"})

    # Otherwise it's a create or update
    resource_properties = event['ResourceProperties']

    # Validation of listener_arn and service_name
    if 'listener_arn' not in resource_properties or 'service_name' not in resource_properties:
        return send_response(event, context, "FAILED", {"Message": "Missing listener_arn and service_name parameters from CloudFormation"})

    # Json test nested under ResourceProperties
    # {"listener_arn": "arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-dev/12345/6789","service_name": "lcg-fakeservice.lcg.com"}
    listener_arn = resource_properties['listener_arn']
    service_name = resource_properties['service_name']
    
    # Look for the service priority in the listener if it already exists
    service_priority = get_service_priority(service_name, listener_arn)

    # Service already exists, re-use the same priority
    if service_priority != -1:
        print("Found existing service, returning " + str(service_priority))
        return send_response(event, context, "SUCCESS", ({ 'priority': '' + str(service_priority) +'' }))

    # Find a new rule priority for the new service (preliminary)
    service_priority_preliminary = get_next_avail_priority(listener_arn)

    # Wait 5 seconds and see if the priority has changed, if it has this means that the new service priority is now in use and we need to return a new one
    time.sleep(5)

    # Find a new rule priority for the new service (preliminary)
    service_priority_final = get_next_avail_priority(listener_arn)

    while service_priority_final != service_priority_preliminary:
        service_priority_preliminary = get_next_avail_priority(listener_arn)
        time.sleep(5)
        service_priority_final = get_next_avail_priority(listener_arn)

    # Return the final service priority
    service_priority = service_priority_final

    print("Returning rule priority " + str(service_priority) + " for service " + service_name)

    # Limit of 50000
    # see https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_CreateRule.html
    if service_priority > 50000:
        return send_response(event, context, "FAILED", {"Message": "Load balancer has reached its rule priority limit, provision a different load balancer"})

    return send_response(event, context, "SUCCESS", ({ 'priority': '' + str(get_next_avail_priority(listener_arn)) +'' }))

################### Lambda handler for non custom backed resource #################
def lambda_handler(event, context):
    
    # Json test body
    # {"listener_arn": "arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-dev/12345/6789","service_name": "lcg-fakeservice.lcg.com"}
    
    if 'listener_arn' not in event or 'service_name' not in event:
        return {
            'statusCode': 400,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({ 'error': 'Incorrect parameters, you need to define listener_arn and service_name' })
        }
    
    listener_arn = event['listener_arn']
    service_name = event['service_name']
    
    # listener_arn = 'arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-dev/12345/6789'
    # service_name = 'lcg-fakeservice.lcg.com'
    
    # TEST - 'arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-test/9e6057f88db2df10/9877b35b1c193ed8'
    # DEV - 'arn:aws:elasticloadbalancing:eu-west-1:FakeAccount123:listener/app/lcg-infra-ecs-dev/12345/6789'

    # Does the stack exist?
    #stack_name = 'lcg-infra-ecs-dev'
    #stack_exists = find_stack(stack_name)
    #if stack_exists:
    #    print("Found stack!")
    #else:
    #    print("Stack does not exist!")

    # Look for the service priority in the listener if it already exists
    service_priority = get_service_priority(service_name, listener_arn)
    
    # Service already exists, re-use the same priority
    if service_priority != -1:
        print("Found existing service, returning " + str(service_priority))
        return {
            'statusCode': 200,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({ 'priority': '' + str(service_priority) +'' })
        }
        
    # Find a new rule priority for the new service
    service_priority = get_next_avail_priority(listener_arn)
    print("Returning rule priority " + str(service_priority) + " for service " + service_name)

    # Limit of 50000
    # see https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_CreateRule.html
    if service_priority > 50000:
        return {
            'statusCode': 200,
            'headers': { 'Content-Type': 'application/json' },
            'body': json.dumps({ 'priority': '' + str("Load balancer has reached its rule priority limit, provision a different load balancer") +'' })
        }

    return {
         'statusCode': 200,
         'headers': { 'Content-Type': 'application/json' },
         'body': json.dumps({ 'priority': '' + str(service_priority) +'' })
    }

#### Returns next available priority to use for a listener ####
def get_next_avail_priority(listener_arn):
    
    client = boto3.client('elbv2')
    rules = client.describe_rules(
        ListenerArn=listener_arn,
    )['Rules']

    rules = [rule for rule in rules if rule['Priority'].isdigit()]

    # No rules are in use, return 1
    if not rules:
        return 1

    sorted_rules = sorted(rules, key=lambda x: int(x['Priority']), reverse=False)
    # Transform to flat structure
    number_sequence = []
    for rule in sorted_rules:
        number_sequence.append(int(rule['Priority']))
    
    # Test cases
    #number_sequence = [1, 2, 3, 4, 5, 6, 7, 101, 102, 203, 206, 207, 208, 209, 210, 212, 301, 302]
    #number_sequence = [101, 102]
    print(number_sequence)
    
    # 1 is not used yet, so use 1
    if 1 not in number_sequence:
        return 1
        
    diff_between_elements = [j-i for i, j in zip(number_sequence[:-1], number_sequence[1:])]
    for diff in diff_between_elements:
        number_sequence.append(int(rule['Priority']))  
    #print(diff_between_elements)
    index = 0
    if len(diff_between_elements) == 0:
        return 2 # Only 1 rule so the next rule priority is 2
    for x in diff_between_elements:
        if x != 1:
            break
        else:
            index = index + 1
    
    priority = int(number_sequence[index])+1

    return priority    

#### Returns rule priority of a service name in the host header property ####
def get_service_priority(service_name, listener_arn):
    client = boto3.client('elbv2')
    # Service name
    rules = client.describe_rules(
        ListenerArn=listener_arn,
    )['Rules']
    for rule in rules:
        #print(rule)
        if (len(rule['Conditions']) > 0):
            conditions = (rule['Conditions'])[0]
            host_header = (conditions['Values'])[0]
            if host_header == service_name:
                # print(rule['Priority'] + " " + (conditions['Values'])[0])
                return int(rule['Priority'])
    
    return -1

#### Checks if a stack exists ####
def find_stack(stack_name):
    cf_conn = boto3.client('cloudformation')
    filterList = ["CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_IN_PROGRESS", "UPDATE_ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_IN_PROGRESS"]
    resp = cf_conn.list_stacks()
    #print(resp['StackSummaries'])
    # Initial request
    for stack in resp['StackSummaries']:
        status = stack['StackStatus']
        if status in filterList:
            #print(stack['StackName'])
            if stack_name == stack['StackName']:
                return True

    # Check for next token (pagination)
    while 'NextToken' in resp:
        resp = cf_conn.list_stacks(NextToken=resp['NextToken'])
        for stack in resp['StackSummaries']:
            status = stack['StackStatus']
            #print(stack)
            if status in filterList:
                #print(stack['StackName'])
                if stack_name == stack['StackName']:
                    return True
        
    return False

### Send response function 
### From https://github.com/stelligent/cloudformation-custom-resources/blob/master/lambda/python/customresource.py
def send_response(event, context, response_status, response_data):
    # Send a resource manipulation status response back to CloudFormation
    # Sample response
    # {
    #     "Status": "SUCCESS",
    #     "Reason": "See the details in CloudWatch Log Stream: 2019/03/04/[$LATEST]Fake-ResourceId",
    #     "PhysicalResourceId": "2019/03/04/[$LATEST]Fake-ResourceId",
    #     "StackId": "arn:aws:cloudformation:eu-west-1:FakeAccount123:stack/LambdaFunction/SomeId",
    #     "RequestId": "fake-requestId",
    #     "LogicalResourceId": "LambdaFunction",
    #     "Data": {
    #         "priority": "8"
    #     }
    # }
    # Format of this request is defined at https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/crpg-ref-responses.html

    response_body = json.dumps({
        "Status": response_status,
        "Reason": "See the details in CloudWatch Log Stream: " + context.log_stream_name,
        "PhysicalResourceId": context.log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })

    print("ResponseURL: " + str(event['ResponseURL']))
    print("ResponseBody: " + response_body)
    req = requests.put(event['ResponseURL'], data=response_body)
    print("Status code: " + str(req.status_code))
