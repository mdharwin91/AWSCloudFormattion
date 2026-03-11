import boto3
import os

# Load configuration from environment variables
INSTANCE_ID = os.environ.get('INSTANCE_ID')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=REGION)
ec2_client = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

def lambda_handler(event, context):
    """
    Lambda handler to automatically stop EC2 instance and send notification via SNS.
    """
    try:
        if not INSTANCE_ID or not SNS_TOPIC_ARN:
            raise ValueError("INSTANCE_ID or SNS_TOPIC_ARN environment variables not set")
        
        instance = ec2_resource.Instance(INSTANCE_ID)
        current_status = instance.state.get('Name')
        print(f"CURRENT STATUS: {current_status}")
        
        message = "EC2 is already STOPPED !!!"
        
        if current_status == "running":
            ec2_client.stop_instances(InstanceIds=[INSTANCE_ID])
            message = "EC2 Status changed to: STOPPED"
            print(f"Instance {INSTANCE_ID} stopped successfully")
        else:
            print(f"Instance {INSTANCE_ID} is already stopped")
        
        # Publish notification
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject='EC2 Notification [INSTANCE AUTO STOP]: ' + message
        )
        
        return {
            'statusCode': 200,
            'body': message
        }
    except Exception as e:
        error_message = f"Error in auto-stop function: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': error_message
        } 