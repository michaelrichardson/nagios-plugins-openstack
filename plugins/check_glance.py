#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Keystone monitoring script for Nagios
#
# Copyright © 2012 eNovance <licensing@enovance.com>
#
# Author: Florian Lambert <florian.lambert@enovance.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import sys
import argparse

from keystoneclient.v2_0 import client as ksclient
import glanceclient as glance_client
from utils import EnvDefault

STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

def collect_args():

  parser = argparse.ArgumentParser(description='Check an OpenStack glance server.')
  parser.add_argument('--auth_url', metavar='URL', type=str, required=True,
        action=EnvDefault, envvar='OS_AUTH_URL', help='Keystone URL')
  parser.add_argument('--username', metavar='username', type=str, required=True,
        action=EnvDefault, envvar='OS_USERNAME', help='username to use for authentication')
  parser.add_argument('--password', metavar='password', type=str, required=True,
        action=EnvDefault, envvar='OS_PASSWORD', help='password to use for authentication')
  parser.add_argument('--tenant', metavar='tenant', type=str, required=True,
        action=EnvDefault, envvar='OS_TENANT_NAME', help='tenant name to use for authentication')
  parser.add_argument('--req_count', metavar='numberImages', type=str,
        required=False,
        help='minimum number of images in glance')
  parser.add_argument('--req_images', metavar='imagesName', type=str, nargs='+',
        required=False,
        help='name of images who must be available')
  parser.add_argument('--region_name', metavar='region_name', type=str,
        action=EnvDefault, envvar='OS_REGION_NAME', help='Region to select for authentication')
  parser.add_argument('--ca-cert', metavar='ca_cert', type=str,
                    action=EnvDefault, envvar='OS_CACERT', help='Location of the CA cert for validation')
  parser.add_argument('--insecure', action='store_true', default=False,
                    help='Do not verify certificates')
  return parser



def check_glance(c,args):
  #Flags resultat
  valid_image = 0
  count = 0


  if args.req_count:
    required_count = int(args.req_count)
    if len(list(c.images.list(**{"limit": required_count}))) >= required_count:
      count = 1

  #filters = {}
  #filters['name'] = "Debian GNU/Linux 6.0.4 amd64"
  #filters['container_format'] = "ami"

  if args.req_images:
    required_images = args.req_images

    for image in required_images:
      try:
        if len(list(c.images.list(**{"filters": {"name": image}}))) == 1:
          valid_image = valid_image + 1
      except :
        pass

  #parameters = {"filters": filters, "limit": limit}
  #images = c.get_images(**parameters)


  if args.req_count and count == 0:
    print "Failed - less than %d images found" % (required_count)
    sys.exit(STATE_CRITICAL)


  if args.req_images and valid_image < len(required_images):
    print "Failed - '%s' %d/%d images found " % (required_images, valid_image, len(required_images))
    sys.exit(STATE_WARNING)


  if args.req_images and args.req_count:
    print "OK - image %s found and enough images >=%d" % (required_images, required_count)
  elif args.req_images:
    print "OK - image %s found" % required_images
  elif args.req_count:
    print "OK - more than %d images found" % required_count
  else :
    print "OK - Connection glance established"


if __name__ == '__main__':
  args = collect_args().parse_args()
  try:
    ks_client = ksclient.Client(username=args.username,
                                password=args.password,
                                tenant_name=args.tenant,
                                auth_url=args.auth_url,
                                cacert=args.ca_cert,
                                insecure=args.insecure)

    token = ks_client.auth_token
    endpoint = ks_client.service_catalog.url_for(service_type='image')

    c = glance_client.Client('1', endpoint, token=token, cacert=args.ca_cert, insecure=args.insecure)
    sys.exit(check_glance(c, args))
  except Exception as e:
    print str(e)
    sys.exit(STATE_CRITICAL)
