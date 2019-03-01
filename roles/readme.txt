Enables use of sessions manager for EC2 instances

1. Attach the permissions defined in the .json file to your EC2 instance
2. From web console, access Systems Manager Service.
3. Click Session Manager and then click “Start Session”
4. In the next window, select the instance and click “Start Session”
5. The OS console window opens and you are able to execute any command on the instance.
6. You can also access the instance with AWS CLI. 
You first need to install the Session Manager Plugin for the AWS CLI. Instructions on how to do that can be found here: 
https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

Then you just simply run the command below from your Command prompt on your machine:

aws --profile your-aws-profile ssm start-session --target id-of-an-instance-you-want-to-access

example:  aws --profile myaccount-dev ssm start-session --target i-0f04fbf89b4f7d314