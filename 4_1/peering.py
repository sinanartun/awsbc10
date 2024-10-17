import boto3
import sys
from loguru import logger
import json
import time



logger.remove()

logger.add(
    sink=sys.stdout,
    format="<level>{time:HH:mm:ss}</level> | <level>{level: <8}</level>:{line} | <level>{message}</level>",
    level="DEBUG"
)
common_regions = ['eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1']

def create_vpc(region_name, c):
    vpcs = {}
    # Create an EC2 client
    ec2 = boto3.client('ec2', region_name=region_name)
    vpcs['region_name'] = region_name
    response = ec2.describe_availability_zones()
    zone_names = [zone['ZoneName'] for zone in response['AvailabilityZones']]
    # Create a VPC
    cidr = '10.' + str(c) + '.0.0/16'

    vpcs['cidr'] = '10.' + str(c) + '.0.0/16'

    vpc = ec2.create_vpc(
        CidrBlock=cidr
    )

    # Wait for the VPC to be available
    waiter = ec2.get_waiter('vpc_available')
    waiter.wait(VpcIds=[vpc['Vpc']['VpcId']])

    logger.info("Created VPC with ID: {}", vpc['Vpc']['VpcId'])

    vpcs['VpcId'] = vpc['Vpc']['VpcId']

    # Enable DNS support for the VPC
    ec2.modify_vpc_attribute(
        VpcId=vpc['Vpc']['VpcId'],
        EnableDnsSupport={'Value': True}
    )

    # Enable DNS hostnames for the VPC
    ec2.modify_vpc_attribute(
        VpcId=vpc['Vpc']['VpcId'],
        EnableDnsHostnames={'Value': True}
    )

    # Create an Internet Gateway
    igw = ec2.create_internet_gateway()

    logger.info("Created Internet Gateway with ID: {}", igw['InternetGateway']['InternetGatewayId'])

    # Attach the Internet Gateway to the VPC
    ec2.attach_internet_gateway(
        InternetGatewayId=igw['InternetGateway']['InternetGatewayId'],
        VpcId=vpc['Vpc']['VpcId']
    )

    vpcs['InternetGatewayId'] = igw['InternetGateway']['InternetGatewayId']

    # Create three subnets in the VPC
    subnet1 = ec2.create_subnet(
        VpcId=vpc['Vpc']['VpcId'],
        CidrBlock='10.' + str(c) + '.0.0/24',
        AvailabilityZone=zone_names[0]
    )

    waiter = ec2.get_waiter('subnet_available')
    waiter.wait(
        SubnetIds=[subnet1['Subnet']['SubnetId']],
        Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            }
        ],
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 120
        }
    )
    vpcs['Subnets'] = []
    vpcs['Subnets'].append(subnet1['Subnet']['SubnetId'])

    logger.info("Created Subnet 1 with ID: {}", subnet1['Subnet']['SubnetId'])

    subnet2 = ec2.create_subnet(
        VpcId=vpc['Vpc']['VpcId'],
        CidrBlock='10.' + str(c) + '.1.0/24',
        AvailabilityZone=zone_names[1]
    )

    waiter.wait(
        SubnetIds=[subnet2['Subnet']['SubnetId']],
        Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            }
        ],
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 120
        }
    )

    vpcs['Subnets'].append(subnet2['Subnet']['SubnetId'])

    logger.info("Created Subnet 2 with ID: {}", subnet2['Subnet']['SubnetId'])

    subnet3 = ec2.create_subnet(
        VpcId=vpc['Vpc']['VpcId'],
        CidrBlock='10.' + str(c) + '.2.0/24',
        AvailabilityZone=zone_names[2]
    )

    waiter.wait(
        SubnetIds=[subnet3['Subnet']['SubnetId']],
        Filters=[
            {
                'Name': 'state',
                'Values': ['available']
            }
        ],
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 120
        }
    )

    vpcs['Subnets'].append(subnet3['Subnet']['SubnetId'])

    logger.info("Created Subnet 3 with ID: {}", subnet3['Subnet']['SubnetId'])

    # Create a route table for the VPC
    route_table = ec2.create_route_table(VpcId=vpc['Vpc']['VpcId'])

    vpcs['RouteTableId'] = route_table['RouteTable']['RouteTableId']

    logger.info("Created Route Table with ID: {}", route_table['RouteTable']['RouteTableId'])

    # Create a route to the Internet Gateway in the route table
    ec2.create_route(
        DestinationCidrBlock='0.0.0.0/0',
        GatewayId=igw['InternetGateway']['InternetGatewayId'],
        RouteTableId=route_table['RouteTable']['RouteTableId']
    )

    logger.info("Created route to Internet Gateway in Route Table")

    # Associate the subnets with the route table
    ec2.associate_route_table(
        SubnetId=subnet1['Subnet']['SubnetId'],
        RouteTableId=route_table['RouteTable']['RouteTableId']
    )

    ec2.associate_route_table(
        SubnetId=subnet2['Subnet']['SubnetId'],
        RouteTableId=route_table['RouteTable']['RouteTableId']
    )

    ec2.associate_route_table(
        SubnetId=subnet3['Subnet']['SubnetId'],
        RouteTableId=route_table['RouteTable']['RouteTableId']
    )

    logger.info("Associated subnets with Route Table")

    return vpcs


def create_peering(vpc1, vpc2):
    region_name_1 = vpc1['region_name']
    region_name_2 = vpc2['region_name']
    ec2_client_1 = boto3.client('ec2', region_name=region_name_1)
    ec2_client_2 = boto3.client('ec2', region_name=region_name_2)

    # specify the IDs of the VPCs that we want to connect
    vpc_id_1 = vpc1['VpcId']
    vpc_id_2 = vpc2['VpcId']

    # create the VPC peering connection
    response = ec2_client_1.create_vpc_peering_connection(
        VpcId=vpc_id_1,
        PeerVpcId=vpc_id_2,
        PeerRegion=region_name_2
    )


    peering_connection_id = response['VpcPeeringConnection']['VpcPeeringConnectionId']
    # create a waiter to wait for the VPC peering connection to become available
    waiter1 = ec2_client_1.get_waiter('vpc_peering_connection_exists')

    # wait for the VPC peering connection to become pending-acceptance
    waiter1.wait(
        VpcPeeringConnectionIds=[peering_connection_id],
        Filters=[
            {
                'Name': 'status-code',
                'Values': ['pending-acceptance','failed']
            }
        ],
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 120
        }
    )

    logger.success(f'Peering connection request made successfully from {region_name_1}:{vpc_id_1} -> {region_name_2}:{vpc_id_2}')

    waiter2 = ec2_client_2.get_waiter('vpc_peering_connection_exists')
    waiter2.wait(
        VpcPeeringConnectionIds=[peering_connection_id],
        Filters=[
            {
                'Name': 'status-code',
                'Values': ['pending-acceptance', 'failed']
            }
        ],
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 120
        }
    )

    # accept the VPC peering connection on the peer VPC
    response = ec2_client_2.accept_vpc_peering_connection(
        VpcPeeringConnectionId=peering_connection_id
    )

    # create a waiter to wait for the VPC peering connection to become "active" in the peer VPC
    waiter3 = ec2_client_2.get_waiter('vpc_peering_connection_exists')

    # wait for the VPC peering connection to become "active" in the peer VPC
    waiter3.wait(
        VpcPeeringConnectionIds=[peering_connection_id],
        Filters=[
            {
                'Name': 'status-code',
                'Values': ['active']
            }
        ],
        WaiterConfig={
            'Delay': 1,
            'MaxAttempts': 120
        }
    )

    # print the ID of the new VPC peering connection
    logger.info('Created VPC peering connection with ID: ' + peering_connection_id)
    route_table_id_1 = vpc1['RouteTableId']
    destination_cidr_block_2 = vpc2['cidr']
    add_route_to_peering(vpc_id_1, route_table_id_1, destination_cidr_block_2, peering_connection_id, region_name_1)

    route_table_id_2 = vpc2['RouteTableId']
    destination_cidr_block_1 = vpc1['cidr']
    add_route_to_peering(vpc_id_1, route_table_id_2, destination_cidr_block_1, peering_connection_id, region_name_2)

def add_route_to_peering(vpc_id, route_table_id, destination_cidr_block, peering_connection_id, region_name):
    ec2 = boto3.client('ec2', region_name=region_name)
    response = ec2.create_route(
        DestinationCidrBlock=destination_cidr_block,
        RouteTableId=route_table_id,
        VpcPeeringConnectionId=peering_connection_id,
    )
    # Wait for the route to become active
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        try:
            response = ec2.describe_route_tables(RouteTableIds=[route_table_id])
            for route_table in response['RouteTables']:
                for route in route_table['Routes']:
                    if route.get('DestinationCidrBlock') == destination_cidr_block:
                        if route.get('State') == 'active':
                            logger.success(f"Route {destination_cidr_block} to VPC peering connection {peering_connection_id} is now active.")
                            return
                        else:
                            logger.warning(f"Route {destination_cidr_block} to VPC peering connection {peering_connection_id} is still being propagated...")
                            break
            attempts += 1
            time.sleep(3)
        except Exception as e:
            logger.warning(f"An error occurred: {e}")
            attempts += 1
            time.sleep(3)

    logger.critical(f"Route {destination_cidr_block} to VPC peering connection {peering_connection_id} did not become active within the allotted time.")

def create_peering_connections(all_vpc):
    matrix = []

    for i, vpc1 in enumerate(all_vpc):
        for j, vpc2 in enumerate(all_vpc):
            if i != j:
                if len(matrix) < 1:
                    matrix.append(list([i,j]))
                    continue
                exist = False
                for mat in list(matrix):
                    if (list([i,j]) == mat) or (list([j,i]) == mat) :
                        exist = True
                if exist == False:
                    matrix.append(list([i, j]))
                    continue

    logger.info(len(matrix))
    logger.info(json.dumps(matrix))

    for mat in list(matrix):
        create_peering(all_vpc[mat[0]],all_vpc[mat[1]])


def run():
    all_vpc = []
    for c, region_name in enumerate(common_regions):
        vpc_row = create_vpc(region_name, c)
        all_vpc.append( vpc_row)

    # logger.info(json.dumps(all_vpc, indent=2, sort_keys=True, default=str))
    with open('all_vpc.json', 'w') as f:
        json.dump(all_vpc, f)

    with open('all_vpc.json') as f:
        json_data = f.read()

    # Convert the JSON data to a Python object
    all_vpc = json.loads(json_data)
    # logger.success("VPCs created successfully")
    create_peering_connections(all_vpc)


run()