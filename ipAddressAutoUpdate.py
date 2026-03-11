import json
import boto3
import os
from botocore.exceptions import ClientError
import copy

# Load configuration from environment variables
INSTANCE_ID = os.environ.get('INSTANCE_ID')
SECURITY_GROUP_ID = os.environ.get('SECURITY_GROUP_ID')
REGION = os.environ.get('AWS_REGION', 'ap-south-1')

# Initialize AWS clients
ec2_client = boto3.client('ec2', region_name=REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

# Get VPC ID
response = ec2_client.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')

def lambda_handler(event, context):
    """
    Lambda handler to update security group with client IP address.
    Gets the IP from query string parameters and authorizes it in the security group.
    """
    try:
        if not INSTANCE_ID or not SECURITY_GROUP_ID:
            raise ValueError("INSTANCE_ID or SECURITY_GROUP_ID environment variables not set")
        
        url = "INSTANCE STOPPED"
        print(f"Event: {event}")
        
        # Get IP address from query parameters
        client_ip = event.get("queryStringParameters", {}).get("ip", "")
        if not client_ip:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'IP address not provided'})
            }
        
        client_ip_cidr = f"{client_ip}/32"
        print(f"Client IP: {client_ip_cidr}")
        
        # Check instance status
        instance = ec2_resource.Instance(INSTANCE_ID)
        current_status = instance.state.get('Name')
        print(f"CURRENT STATUS: {current_status}")
        
        if current_status == "running":
            # Get EC2 public IP and DNS
            inst_details = ec2_client.describe_instances(InstanceIds=[INSTANCE_ID])
            print(f"INSTANCE DETAILS: {inst_details}")
            public_dns = inst_details['Reservations'][0]['Instances'][0]['PublicDnsName']
            url = f"http://{public_dns}"
        
        # Update the security group with client IP
        response = ec2_client.describe_security_groups(GroupIds=[SECURITY_GROUP_ID])
        group = response['SecurityGroups'][0]
        
        for permission in group['IpPermissions']:
            new_permission = copy.deepcopy(permission)
            ip_ranges = new_permission.get('IpRanges', [])
            
            for ip_range in ip_ranges:
                if ip_range.get('Description') == 'My School IP':
                    ip_range['CidrIp'] = client_ip_cidr
            
            # Revoke old permission and authorize new one
            ec2_client.revoke_security_group_ingress(GroupId=group['GroupId'], IpPermissions=[permission])
            ec2_client.authorize_security_group_ingress(GroupId=group['GroupId'], IpPermissions=[new_permission])
        
        print(url)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'url': url, 'message': 'Security group updated with new IP'})
        }
    except Exception as e:
        error_message = f"Error in IP update function: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_message})
        }


