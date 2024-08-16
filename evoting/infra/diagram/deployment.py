from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import ECS
from diagrams.aws.network import ELB, Route53, VPC, PrivateSubnet, PublicSubnet
from diagrams.aws.database import RDS
from diagrams.aws.security import WAF
from diagrams.aws.storage import S3
from diagrams.aws.management import Cloudwatch

environment_name = "dev"
service_name = "django-server"
load_balancer_dns = "elects-Publi-d6EMd60hLUg0-972429885.ap-southeast-1.elb.amazonaws.com"
service_endpoint = "https://elect-sg.cookndrum.com"
service_discovery = "django-server.dev.electsg.local:8000"
db_host = "djangodb.cj8ug0qq88oo.ap-southeast-1.rds.amazonaws.com"
s3_bucket = "elect-sg-bucket"
ringct_service = "ringct-service:50051"
vpc_id = "vpc-05e3f571c69b10978"
public_subnets = ["subnet-018e237f6c1ccc553", "subnet-02f497121cd086338"]
private_subnets = ["subnet-0245f136b4ccbf00a", "subnet-09b75374054a5de3c"]

with Diagram("AWS Copilot Architecture with VPC", show=False):
    dns = Route53("DNS")
    lb = ELB("Load Balancer")
    waf = WAF("WAF")

    with Cluster("VPC"):
        vpc = VPC("VPC")

        with Cluster("Public Subnets"):
            public_subnet1 = PublicSubnet("Public Subnet 1")
            public_subnet2 = PublicSubnet("Public Subnet 2")

        with Cluster("Private Subnets"):
            private_subnet1 = PrivateSubnet("Private Subnet 1")
            private_subnet2 = PrivateSubnet("Private Subnet 2")

        with Cluster("Services"):
            django_server = ECS("django-server")
            ringct_service = ECS("ringct-service")

        with Cluster("Database"):
            db = RDS("Django DB")

        s3 = S3("S3 Bucket")
        alarm = Cloudwatch("Rollback Alarm")

        dns >> waf >> lb >> [public_subnet1, public_subnet2] >> django_server
        django_server >> private_subnet1 >> db
        django_server >> s3
        django_server >> ringct_service
        ringct_service >> db
        alarm >> django_server
