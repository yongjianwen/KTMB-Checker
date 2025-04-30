import logging
import os

import boto3
from dotenv import load_dotenv

load_dotenv()
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger('bot')


def upload_file_to_s3(file_path, bucket_name, s3_key):
    s3_client = boto3.client(
        service_name='s3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    try:
        s3_client.upload_file(file_path, bucket_name, s3_key)
        logger.info('>> Upload file successfully')
    except Exception as e:
        logger.info(f'>> Error uploading file: {e}')
        return False

    return True


def download_file_from_s3(bucket_name, s3_key, local_path):
    s3_client = boto3.client(
        service_name='s3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )

    try:
        s3_client.download_file(bucket_name, s3_key, local_path)
        logger.info('>> Download file successfully')
    except Exception as e:
        logger.info(f'>> Error downloading file: {e}')
        return False

    return True
