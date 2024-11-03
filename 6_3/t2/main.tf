provider "aws" {
  region = "eu-north-1"
  profile = "sinanartun.com"
}


variable "region" {
  type    = string
  default = "eu-north-1"
}

variable "aws_profile" {
  type    = string
  default = "sinanartun.com"
}

resource "aws_s3_bucket" "mybucket" {
  bucket = "awsbc10-${var.region}"

  
}

resource "aws_s3_bucket_public_access_block" "mybucket_block" {
  bucket                  = aws_s3_bucket.mybucket.id
  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_website_configuration" "mybucket_configuration" {
  bucket = aws_s3_bucket.mybucket.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}
resource "aws_s3_bucket_policy" "mybucket_policy" {
  bucket = aws_s3_bucket.mybucket.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid       = "AllowPublicRead",
        Effect    = "Allow",
        Principal = "*",
        Action    = ["s3:GetObject"],
        Resource  = ["${aws_s3_bucket.mybucket.arn}/*"]
      }
    ]
  })
  
  depends_on = [aws_s3_bucket_public_access_block.mybucket_block]
}
