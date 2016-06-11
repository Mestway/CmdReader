#!/usr/bin/python2.4
# -*- coding: utf-8 -*-
#
# Copyright (C) 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Simple command-line example for Custom Search.

Command-line application that does a search.
"""

__author__ = 'jcgregorio@google.com (Joe Gregorio)'

# import pprint
import os, sys
from apiclient.discovery import build

def print_result(res, result_id):
    for result in res[u'items']:
        print("%d.%s\n" % (result_id, result['title'].encode('utf-8')))
        print("%s\n" % result['link'])
        print("%s\n\n" % result['snippet'].encode('utf-8'))
        result_id += 1

def main():
  # Build a service object for interacting with the API. Visit
  # the Google APIs Console <http://code.google.com/apis/console>
  # to get an API key for your own application.
  service = build("customsearch", "v1",
                  developerKey="AIzaSyA049kTJjSL8DotsLVf4rSKdc0wuVrsV0M")
  Search_Engine_ID = "001089351014153505670:7jbzwugbvrc"

  query = sys.argv[1]

  print "Searching \"%s\"..." % query
  for i in xrange(5):
      res = service.cse().list(
          q=query.decode('utf-8'),
          cx=Search_Engine_ID,
          start=str(i*10+1)
      ).execute()
      print_result(res, i*10+1)

if __name__ == "__main__":
    main()