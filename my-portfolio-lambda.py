import json
import boto3
import io
import zipfile
import mimetypes


def lambda_handler(event, context):
    # Initialize sns and topic
    sns = boto3.resource('sns')
    topic = sns.Topic(
        'arn:aws:sns:us-east-1:544523340064:deployPortfolioTopic'
    )

    location = {
        'bucketName': 'portfoliobuild.deanunix.com',
        'objectKey': 'buildPortfolio.zip'
    }

    try:
        job = event.get('CodePipeline.job')
        print(job)
        if job:
            for artifact in job['data']['inputArtifacts']:
                if artifact['name'] == 'BuildArtifact':
                    location = artifact['location']['s3Location']

        print(f'Building portfolio from {location}')

        # Initialize S3 Buckets
        s3 = boto3.resource('s3')
        portfolio_bucket = s3.Bucket('portfolio.deanunix.com')
        build_bucket = s3.Bucket(location['bucketName'])

        # Will hold build zip file
        portfolio_zip = io.BytesIO()

        # Download build zip and store it
        build_bucket.download_fileobj(location['objectKey'], portfolio_zip)

        # Unzip build file and upload to specified bucket with public read and
        # intelligent tier
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs={
                    'StorageClass': 'INTELLIGENT_TIERING',
                    'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')

        # Notify by email
        topic.publish(
            Subject='Portfolio Deployed',
            Message='Portfolio deployed successfully!'
        )

        if job:
            codepipeline = boto3.client('codepipeline')
            codepipeline.put_job_success_result(jobId=job['id'])

    except:
        topic.publish(
            Subject='Failed To Deploy Portfolio',
            Message='Something went wrong, the deployment was not successful.')
        raise

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
