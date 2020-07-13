import boto3
import io
import zipfile
import mimetypes

# Initialize S3 Buckets
s3 = boto3.resource('s3')
portfolio_bucket = s3.Bucket('portfolio.deanunix.com')
build_bucket = s3.Bucket('portfoliobuild.deanunix.com')

# Will hold build zip file
portfolio_zip = io.BytesIO()

# Download build zip and store it
build_bucket.download_fileobj('buildPortfolio.zip', portfolio_zip)

# Unzip build file and upload to specified bucket with public read and
# intelligent tier
with zipfile.ZipFile(portfolio_zip) as myzip:
    for nm in myzip.namelist():
        obj = myzip.open(nm)
        portfolio_bucket.upload_fileobj(obj, nm, ExtraArgs={
            'StorageClass': 'INTELLIGENT_TIERING',
            'ContentType': mimetypes.guess_type(nm)[0]})
        portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
