from django.core.management.base import BaseCommand
from myapp.models import District
from . import config
from pygrpc.ringct_client import (
    grpc_generate_user_and_votingcurr_run,
)
import logging
import math

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Create district data and perform related operations'

    def handle(self, *args, **options):
        for district in config.districts_mocked:
            district, created = District.objects.get_or_create(
                district_name=district,
                defaults={'num_of_people': config.voternum_per_district}
            )
            
            if created:
                logger.info(f'Created district: {district}')
            else:
                logger.warning(f'District already exists: {district}')

        # Retrieve all district IDs
        district_ids = District.objects.values_list('district_id', flat=True)

        # Call the gRPC service for each district
        for district_id in district_ids:
            district = District.objects.get(district_id=district_id)
            grpc_generate_user_and_votingcurr_run(district_id=district.district_id, voter_num=math.floor(district.num_of_people*1.1))
            logger.info("Called gRPC service for district: %s", district.district_name)

        logger.info('District creation and related operations completed')
