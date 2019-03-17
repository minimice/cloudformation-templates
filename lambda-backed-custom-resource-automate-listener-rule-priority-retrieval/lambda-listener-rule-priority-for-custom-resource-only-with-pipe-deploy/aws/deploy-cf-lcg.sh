#! /bin/bash

set +x

echo "************************************************************************"
echo "*************************** Deploying **********************************"
echo "************************************************************************"

stackFile=${3:-service.yaml}

STACKSTATUS=$(aws --region eu-west-1 cloudformation describe-stacks --stack-name $1 --output text --query 'Stacks[0].StackStatus' 2> /dev/null)
STATUS=$?

if [ $STATUS -ne 0 ]
then
    echo "*** Creating stack"

    NEXT_WAIT_TIME=0
    MAX_WAIT_TIMES=180
    SLEEP_SECONDS=10



    STACKID=$(aws --region eu-west-1 cloudformation create-stack \
        --stack-name $1 \
        --template-body file://$stackFile \
        --timeout-in-minutes 180 \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags \
        Key=cost-center,Value=2468 \
        Key=created-by,Value=lim-chooi-guan-github-id-minimice-aws-certified-sa \
        Key=team,Value=lcg \
        --parameters file://$2 \
        --output text 2>&1)

    echo $STACKID | grep -q "Error"

    STATUS=$?

    if [ $STATUS -eq 0 ]; then
        echo $STACKID | grep -q "No updates"
        if [ $? -eq 1 ]; then
            echo "*** ERROR - Command failed with reason $STACKID"
            exit 1
        fi
            echo "*** No updates performed, continuing ..."
    fi

    echo "*** Waiting to make sure the stack $STACKID is completed successfully"
    echo "*** This may take up to $(( $MAX_WAIT_TIMES * $SLEEP_SECONDS )) seconds..."

    while [ $NEXT_WAIT_TIME -le $MAX_WAIT_TIMES ]; do
        STATUS=$(aws --region eu-west-1 cloudformation describe-stacks --stack-name $1 --query 'Stacks[0].StackStatus')
        echo $STATUS | grep "ROLLBACK"
        if [ $? -eq 0 ]; then
            echo "*** Stack operation failed. Printing events..."
            aws --region eu-west-1 cloudformation describe-stack-events --stack-name $1 --output text --query 'StackEvents[].{Time:Timestamp,Resource:ResourceType,Status:ResourceStatus,Reason:ResourceStatusReason}'
            echo "*** Waiting for stack to be ready for deletion..."
            aws --region eu-west-1 cloudformation wait stack-create-complete --stack-name $1
            echo "*** Deleting stack..."
            aws --region eu-west-1 cloudformation delete-stack --stack-name $1
            aws --region eu-west-1 cloudformation wait stack-delete-complete --stack-name $1
            exit 1
        fi
        echo $STATUS | grep "COMPLETE"
        if [ $? -eq 0 ]; then
          echo "*** Stack operation completed successfully"
          break
        else
          echo "Current stack status: $STATUS"
        fi
        let "++NEXT_WAIT_TIME" && sleep $SLEEP_SECONDS
    done
else
    echo "*** Updating stack"

    NEXT_WAIT_TIME=0
    MAX_WAIT_TIMES=180
    SLEEP_SECONDS=10

    STACKID=$(aws --region eu-west-1 cloudformation update-stack \
        --stack-name $1 \
        --template-body file://$stackFile \
        --capabilities CAPABILITY_NAMED_IAM \
        --tags \
        Key=cost-center,Value=2468 \
        Key=created-by,Value=lim-chooi-guan-github-id-minimice-aws-certified-sa \
        Key=team,Value=lcg \
        --parameters file://$2 \
        --output text 2>&1)
        

    echo $STACKID | grep -q "Error"

    STATUS=$?

    if [ $STATUS -eq 0 ]; then
        echo $STACKID | grep -q "No updates"
        if [ $? -eq 1 ]; then
            echo "*** ERROR - Command failed with reason $STACKID"
            exit 1
        fi
            echo "*** No updates performed, continuing ..."
    fi

    echo "*** Waiting to make sure the stack $STACKID is completed successfully"
    echo "*** This may take up to $(( $MAX_WAIT_TIMES * $SLEEP_SECONDS )) seconds..."

    while [ $NEXT_WAIT_TIME -le $MAX_WAIT_TIMES ]; do
        STATUS=$(aws --region eu-west-1 cloudformation describe-stacks --stack-name $1 --query 'Stacks[0].StackStatus')
        echo $STATUS | grep "ROLLBACK"
        if [ $? -eq 0 ]; then
            echo "*** Stack operation failed. Printing events..."
            aws --region eu-west-1 cloudformation describe-stack-events --stack-name $1 --output text --query 'StackEvents[].{Time:Timestamp,Resource:ResourceType,Status:ResourceStatus,Reason:ResourceStatusReason}'
            echo "*** Rolling back stack..."
            aws --region eu-west-1 cloudformation wait stack-update-complete --stack-name $1
            exit 1
        fi
        echo $STATUS | grep "COMPLETE"
        if [ $? -eq 0 ]; then
          echo "*** Stack operation completed successfully"
          break
        else
          echo "Current stack status: $STATUS"
        fi
        let "++NEXT_WAIT_TIME" && sleep $SLEEP_SECONDS

        if [ $NEXT_WAIT_TIME -ge $MAX_WAIT_TIMES ] && [ $STATUS != "COMPLETE" ]; then
          # We have reached the max wait time and we are not yet complete
          echo "*** Stack has not yet stabilized in $(( $MAX_WAIT_TIMES * $SLEEP_SECONDS )) seconds"
          echo "*** Printing events..."
          aws --region eu-west-1 cloudformation describe-stack-events --stack-name $1 --output text --query 'StackEvents[].{Time:Timestamp,Resource:ResourceType,Status:ResourceStatus,Reason:ResourceStatusReason}'
          echo "*** Rolling back stack..."
          aws --region eu-west-1 cloudformation cancel-update-stack --stack-name $1
          aws --region eu-west-1 cloudformation wait stack-update-complete --stack-name $1
          exit 1
        fi
    done
fi

echo "************************************************************************"
echo "********************** Successfully deployed ***************************"
echo "************************************************************************"
