# CloudFormation Deployment Guide

This guide explains how to deploy your AWS Lambda functions using CloudFormation.

## Overview

Your project contains three Lambda functions for EC2 automation:

1. **instanceAutoStop.py** - Automatically stops EC2 instances at scheduled times
2. **instanceStartStop.py** - Starts or stops EC2 instances based on schedule
3. **ipAddressAutoUpdate.py** - Updates security groups with client IP addresses via API

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured
- Python 3.13 runtime support
- SNS topic created for notifications
- EC2 instance and security group already created

## File Structure

```
AWSCloudFormattion/
├── Lambda.yaml                    # CloudFormation template
├── instanceAutoStop.py            # Auto-stop Lambda function
├── instanceStartStop.py           # Start/stop Lambda function
├── ipAddressAutoUpdate.py         # IP update Lambda function
├── requirements.txt               # Python dependencies
└── DEPLOYMENT_GUIDE.md           # This file
```

## Step 1: Update Configuration

Edit `Lambda.yaml` and update the Parameters section with your AWS details:

```yaml
Parameters:
  InstanceId:
    Default: i-YOUR-INSTANCE-ID
  
  SecurityGroupId:
    Default: sg-YOUR-SECURITY-GROUP-ID
  
  SNSTopicArn:
    Default: arn:aws:sns:ap-south-1:YOUR-ACCOUNT-ID:YOUR-TOPIC-NAME
```

## Step 2: Deploy Stack

### Using AWS CLI

```bash
# Create the stack
aws cloudformation create-stack \
  --stack-name my-ec2-automation \
  --template-body file://Lambda.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=InstanceId,ParameterValue=i-YOUR-INSTANCE-ID \
    ParameterKey=SecurityGroupId,ParameterValue=sg-YOUR-SECURITY-GROUP-ID \
    ParameterKey=SNSTopicArn,ParameterValue=arn:aws:sns:ap-south-1:YOUR-ACCOUNT-ID:YOUR-TOPIC-NAME

# Monitor stack creation
aws cloudformation describe-stacks --stack-name my-ec2-automation
```

### Using AWS Console

1. Go to **CloudFormation** → **Create Stack**
2. Upload the `Lambda.yaml` file
3. Enter stack name: `my-ec2-automation`
4. Fill in parameter values
5. Acknowledge IAM role creation
6. Review and create

## Step 3: Verify Deployment

### Check Stack Status

```bash
aws cloudformation describe-stacks \
  --stack-name my-ec2-automation \
  --query 'Stacks[0].StackStatus'
```

### List Created Resources

```bash
aws cloudformation list-stack-resources \
  --stack-name my-ec2-automation
```

### Get Function ARNs

```bash
aws cloudformation describe-stacks \
  --stack-name my-ec2-automation \
  --query 'Stacks[0].Outputs'
```

## Step 4: Test Functions

### Test Auto-Stop Function

```bash
aws lambda invoke \
  --function-name my-ec2-automation-auto-stop \
  --payload '{}' \
  response.json

cat response.json
```

### Test Start-Stop Function

```bash
aws lambda invoke \
  --function-name my-ec2-automation-start-stop \
  --payload '{}' \
  response.json

cat response.json
```

### Test IP Update Function

```bash
aws lambda invoke \
  --function-name my-ec2-automation-ip-update \
  --payload '{"queryStringParameters":{"ip":"YOUR.CLIENT.IP.ADDRESS"}}' \
  response.json

cat response.json
```

## Step 5: Monitor Function Execution

### View CloudWatch Logs

```bash
# List recent log groups
aws logs describe-log-groups --query 'logGroups[?contains(logGroupName, `lambda`)].logGroupName'

# View logs for a specific function
aws logs tail /aws/lambda/my-ec2-automation-auto-stop --follow

# View specific log stream
aws logs get-log-events \
  --log-group-name /aws/lambda/my-ec2-automation-auto-stop \
  --log-stream-name 'STREAM_NAME'
```

### Check Scheduled Events

```bash
# List EventBridge rules
aws events list-rules --query 'Rules[?contains(Name, `ec2-automation`)]'

# View rule targets
aws events list-targets-by-rule --rule RULE_NAME
```

## Security Best Practices

1. **Use IAM Roles**: Never hardcode AWS credentials
   - Auto-stop function has minimal permissions (stop + SNS)
   - Start-stop and IP update functions have broader EC2 permissions

2. **Environment Variables**: All sensitive data comes from CloudFormation parameters
   - INSTANCE_ID
   - SECURITY_GROUP_ID
   - SNS_TOPIC_ARN
   - AWS_REGION

3. **Least Privilege**: Each function has only required IAM permissions

4. **VPC Configuration**: Optional - add VPC for additional security
   ```yaml
   VpcConfig:
     SecurityGroupIds:
       - sg-xxxxxx
     SubnetIds:
       - subnet-xxxxxx
   ```

5. **Environment Restrictions**: Use EnvironmentTag parameter to distinguish environments

## Updating Configuration

### Update Environment Variables

```bash
aws lambda update-function-configuration \
  --function-name my-ec2-automation-auto-stop \
  --environment 'Variables={INSTANCE_ID=i-new-id,SNS_TOPIC_ARN=arn:aws:sns:...}'
```

### Modify CloudFormation Stack

```bash
aws cloudformation update-stack \
  --stack-name my-ec2-automation \
  --template-body file://Lambda.yaml \
  --capabilities CAPABILITY_IAM \
  --parameters \
    ParameterKey=InstanceId,ParameterValue=i-new-id
```

## Cleanup

### Delete Stack

```bash
aws cloudformation delete-stack --stack-name my-ec2-automation

# Monitor deletion
aws cloudformation wait stack-delete-complete --stack-name my-ec2-automation
```

This will delete all Lambda functions, IAM roles, and the API Gateway.

## Troubleshooting

### Common Issues

**Issue**: Lambda function fails with permission denied
- **Solution**: Verify IAM role has required permissions
- **Action**: Check CloudWatch logs for specific error

**Issue**: SNS notification not received
- **Solution**: Verify SNS topic exists and subscriptions are active
- **Action**: Test SNS directly: `aws sns publish --topic-arn ... --message "test"`

**Issue**: API endpoint returns 404
- **Solution**: API Gateway may not be deployed
- **Action**: Wait 1-2 minutes after stack creation for full deployment

**Issue**: Event scheduling not triggering
- **Solution**: EventBridge rules may be disabled
- **Action**: Check rule status: `aws events list-rules`

## Architecture

```
┌─────────────────────────────────────────┐
│        CloudFormation Stack             │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      Lambda Functions            │  │
│  │  • Auto-Stop (Scheduled)         │  │
│  │  • Start-Stop (Scheduled)        │  │
│  │  • IP Update (API Triggered)     │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      IAM Roles & Policies        │  │
│  │  • InstanceAutoStopRole          │  │
│  │  • EC2ManagementRole             │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │      Events & API Gateway        │  │
│  │  • EventBridge Rules             │  │
│  │  • API Gateway for IP Update     │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
            │
            ├──→ EC2 Instances
            ├──→ Security Groups
            ├──→ SNS Topics
            └──→ CloudWatch Logs
```

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review IAM permissions
3. Verify parameter values
4. Check AWS service limits

## Version Info

- Python Runtime: 3.13
- CloudFormation Version: 2010-09-09
- SAM Version: 2016-10-31
- Last Updated: 2026-03-11
