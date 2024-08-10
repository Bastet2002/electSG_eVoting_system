from diagrams import Diagram, Cluster
from diagrams.aws.compute import ECS
from diagrams.aws.network import ELB, VPC, PrivateSubnet, PublicSubnet
from diagrams.aws.database import RDS
from diagrams.custom import Custom

with Diagram("AWS Copilot Architecture with Horizontal Scaling", show=False):
    lb = ELB("Load Balancer")

    with Cluster("VPC"):
        vpc = VPC("VPC")

        with Cluster("Public Subnets"):
            public_subnet1 = PublicSubnet("Public Subnet 1")
            public_subnet2 = PublicSubnet("Public Subnet 2")

        with Cluster("Private Subnets"):
            private_subnet1 = PrivateSubnet("Private Subnet 1")
            private_subnet2 = PrivateSubnet("Private Subnet 2")

        with Cluster("Services"):
            # Representing multiple instances for horizontal scaling
            django_servers = [ECS(f"Django Server {i}") for i in range(1, 4)]
            ringct_services = [ECS(f"RingCT Service {i}") for i in range(1, 4)]

        with Cluster("Databases"):
            django_db = RDS("Django PostgreSQL")
            ringct_db = RDS("RingCT PostgreSQL")

        singpass_login = ECS("SingPass Login Service")
        singpass_db = RDS("SingPass Mocked PostgreSQL")

        lb >> [public_subnet1, public_subnet2]
        for public_subnet in [public_subnet1, public_subnet2]:
            for django_server in django_servers:
                public_subnet >> django_server
                django_server >> private_subnet1 >> django_db
                django_server >> ringct_services
                singpass_login >> django_server
        for ringct_service in ringct_services:
            ringct_service >> ringct_db
        singpass_login >> singpass_db
