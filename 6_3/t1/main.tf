provider "aws" {
  region = "eu-north-1"
  profile = "sinanartun.com"
}


resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "main-vpc"
  }
}


data "aws_availability_zones" "available" {}

resource "aws_subnet" "public" {
  count                                       = 3
  vpc_id                                      = aws_vpc.main.id
  cidr_block                                  = element(["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24"], count.index)
  map_public_ip_on_launch                     = false
  availability_zone                           = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]
  enable_resource_name_dns_a_record_on_launch = true
  tags = {
    Name = "public-subnet-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count                                       = 3
  vpc_id                                      = aws_vpc.main.id
  cidr_block                                  = element(["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"], count.index)
  availability_zone                           = data.aws_availability_zones.available.names[count.index % length(data.aws_availability_zones.available.names)]
  enable_resource_name_dns_a_record_on_launch = true
  tags = {
    Name = "private-subnet-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "main-igw"
  }
}

resource "aws_route_table_association" "public" {
  count          = 3
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = 3
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}


resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = aws_vpc.main.cidr_block
    gateway_id = "local"
  }

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "public-route-table"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = aws_vpc.main.cidr_block
    gateway_id = "local"
  }

  tags = {
    Name = "private-route-table"
  }
}

resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${aws.region}.s3"
  vpc_endpoint_type = "Gateway"

  route_table_ids = [aws_route_table.private.id]

  tags = {
    Name = "s3-endpoint"
  }
}
