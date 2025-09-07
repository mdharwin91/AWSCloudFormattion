import json
import boto3
from botocore.exceptions import ClientError
import copy
# Client = boto3.resource('ec2')
# ec2 = boto3.client('ec2', region_name='ap-south-1')

ec2 = boto3.client('ec2')
ec2r = boto3.resource('ec2')
response = ec2.describe_vpcs()
vpc_id = response.get('Vpcs', [{}])[0].get('VpcId', '')


SECURITY_GROUP_ID = "sg-04c3c8b63cff84110"
INSTANCE_ID ="i-00e10d36eeb755184"

def lambda_handler(event, context):
    # TODO implement
    
    url = "INSTANCE STOPPED"
    print(event)
    # event = "106.197.105.177"
    event = event["queryStringParameters"]["ip"] + "/32"
    print("INPUT EVENT : ", event)
    
    
    ########. GETTING INSTANCE STATUS
    instance = ec2r.Instance(INSTANCE_ID)
    print("CURRENT STATUS : ", instance.state.get('Name'))
    if instance.state.get('Name') == "running":
        
        ######## GETTING EC2 PUBLIC IP ########
        inst_id = ec2.describe_instances(InstanceIds=[INSTANCE_ID])
        print("INSTANCE DETAILS: ",str(inst_id))
        public_ip = inst_id['Reservations'][0]['Instances'][0]['PublicIpAddress']
        public_dns = inst_id['Reservations'][0]['Instances'][0]['PublicDnsName']
        # print(inst_id)
        print(public_dns)
        # url = "https://"+ public_ip + "/SchoolWeb/Default.aspx"
        url = "http://"+public_dns
    
    ######## UPDATING THE SECURITY GROUP WITH MY IP ########
    response = ec2.describe_security_groups(GroupIds=[SECURITY_GROUP_ID])
    group = response['SecurityGroups'][0]
    for permission in group['IpPermissions']:
        # print("Permission", permission)
        new_permission = copy.deepcopy(permission)
        ip_ranges = new_permission['IpRanges']
        for ip_range in ip_ranges:
            # print("ip_range", ip_range)
            if ip_range['Description'] == 'My School IP':
                # ip_range['CidrIp'] = "%s/32" % new_ip_address
                ip_range['CidrIp'] = event
        ec2.revoke_security_group_ingress(GroupId=group['GroupId'], IpPermissions=[permission])
        ec2.authorize_security_group_ingress(GroupId=group['GroupId'], IpPermissions=[new_permission])
        
    print(url)
    
    return {
        'statusCode': 200,
        'body': json.dumps(url)
    }


