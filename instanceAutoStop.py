import boto3
region = 'ap-south-1'
instances = 'i-00e10d36eeb755184'
SNS_Client = boto3.client('sns')
status_instance = ['i-00e10d36eeb755184']
ec2 = boto3.client('ec2', region_name=region)
ec2r = boto3.resource('ec2', region_name=region)
SNS_ARN = 'arn:aws:sns:ap-south-1:372364834333:Email_Notification_For_Ec2'

def lambda_handler(event, context):
    
    instance = ec2r.Instance(instances)
    print("CURRENT STATUS : ", instance.state.get('Name'))
    message = "EC2 is already STOPPED !!!"
    
    if instance.state.get('Name') == "running":
        ec2.stop_instances(InstanceIds=status_instance)
        message = "EC2 Status changed to : STOPPED"
        response = SNS_Client.publish(
            TopicArn = SNS_ARN,
            Message = message ,
            Subject='Ec2 Notification [INSTANCE AUTO STOP]  : ' + message)
    else:
        print("EC2 is already STOPPED !!!")
    return 