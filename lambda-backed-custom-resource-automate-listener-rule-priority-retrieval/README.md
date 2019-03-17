# Listener Rule Priority Lambda

Lambda function which returns an available listener rule priority to be used when provided with a load balancer listener.

Author: [Lim Chooi Guan](https://www.linkedin.com/in/cgl88/) (Team Cloud Lead @ Scania AB, [AWS Certified Solutions Architect](https://www.certmetrics.com/amazon/public/badge.aspx?i=1&t=c&d=2018-11-08&ci=AWS00446559&dm=80))

## Prerequisites 🛠
* [Python3.7](https://www.python.org/downloads/release/python-370)  
* Love of AWS and the Cloud!  

## Sample Cloudformation template
See *service-template.yaml*
```
  ## This is the magic where it all happens ##
  GetListenerRulePriorityFunctionCustomResource:
    Type: Custom::CustomResource
    Properties:
      ServiceToken: 
        Fn::ImportValue: !Ref GetListenerRulePriorityFunctionArnExportName
      listener_arn:
        Fn::ImportValue: !Ref LoadBalancerListenerExportName
      service_name: !Join ['', [!Ref 'AWS::StackName', ., !Ref PublicHostedZoneDomainName]]
  ListenerRule:
    Type: AWS::ElasticLoadBalancingV2::ListenerRule
    Properties:
      ListenerArn:
        Fn::ImportValue: !Ref LoadBalancerListenerExportName
      ## Automagically retrieve the priority ##
      Priority: 
        !GetAtt GetListenerRulePriorityFunctionCustomResource.priority
    ...
```


