# import pickle
# import os
# import tempfile
# import boto3
# from telegram.ext import PicklePersistence
# from botocore.exceptions import ClientError
#
#
# class S3PicklePersistence(PicklePersistence):
#     def __init__(self, s3_bucket, s3_key, aws_access_key_id=None, aws_secret_access_key=None, region_name=None):
#         """
#         Initialize S3-backed persistence
#
#         Args:
#             s3_bucket: S3 bucket name
#             s3_key: S3 object key (path to file)
#             aws_access_key_id: AWS access key (optional if using IAM roles)
#             aws_secret_access_key: AWS secret key (optional if using IAM roles)
#             region_name: AWS region name
#         """
#         self.s3_bucket = s3_bucket
#         self.s3_key = s3_key
#         self.s3_client = boto3.client(
#             's3',
#             aws_access_key_id=aws_access_key_id,
#             aws_secret_access_key=aws_secret_access_key,
#             region_name=region_name
#         )
#
#         # Initialize with a temporary file that we'll manage
#         self.temp_file = tempfile.NamedTemporaryFile(delete=False)
#         super().__init__(filename=self.temp_file.name, store_user_data=True, store_chat_data=True, store_bot_data=True)
#
#         # Try to load existing data from S3
#         self._load_from_s3()
#
#     def _load_from_s3(self):
#         """Load persistence data from S3"""
#         try:
#             self.s3_client.download_file(self.s3_bucket, self.s3_key, self.temp_file.name)
#             print(f"Successfully loaded persistence data from s3://{self.s3_bucket}/{self.s3_key}")
#         except ClientError as e:
#             if e.response['Error']['Code'] == '404':
#                 print("No existing persistence file found in S3, starting fresh")
#             else:
#                 print(f"Error loading from S3: {e}")
#                 raise
#
#     def _save_to_s3(self):
#         """Save persistence data to S3"""
#         try:
#             self.s3_client.upload_file(self.temp_file.name, self.s3_bucket, self.s3_key)
#             print(f"Successfully saved persistence data to s3://{self.s3_bucket}/{self.s3_key}")
#         except ClientError as e:
#             print(f"Error saving to S3: {e}")
#             raise
#
#     def flush(self):
#         """Save data to S3"""
#         super().flush()  # First save to the local temp file
#         self._save_to_s3()
#
#     def __del__(self):
#         """Clean up temporary file when object is destroyed"""
#         if hasattr(self, 'temp_file') and os.path.exists(self.temp_file.name):
#             os.unlink(self.temp_file.name)