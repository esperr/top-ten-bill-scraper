# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_app]
# [START gae_python3_app]
from flask import Flask, make_response
from bs4 import BeautifulSoup
import requests
#import json
import re
from google.cloud import datastore
from google.cloud import storage
from datetime import datetime
import xml.etree.ElementTree as etree



def find(arr, namestr):
    for x in arr:
        if x["url"] == namestr:
            return x

def getstatus(url):
    r = requests.get(url)
    statusinfo = {}
    if r.status_code != 200:
        print("bad url for: " + url)
    else:
        root = etree.fromstring(r.text)
        sponsorid = root.find('.bill/sponsors/item/bioguideId')
        if sponsorid is not None:
            statusinfo["memberpic"] = "https://www.congress.gov/img/member/" + sponsorid.text.lower() + ".jpg"
        sponsorname = root.find('.bill/sponsors/item/fullName')
        if sponsorname is not None:
            statusinfo["billsponsor"] = sponsorname.text
        #billsummary = root.find('.bill/summaries/billSummaries/item/text')
        #if billsummary is not None:
        #    statusinfo["summarytext"] = billsummary.text
    return statusinfo

def getpic(memberurl):
    memberpage = requests.get(memberurl)
    member_html = BeautifulSoup(memberpage.text, "html.parser")
    picturediv = member_html.find(class_="overview-member-column-picture")
    picurl = picturediv.find_all('a')[0]['href']
    return picurl



def getstatus2(url):
    sponsorinfo = {}
    r = requests.get(url)
    bill_html = BeautifulSoup(r.text, "html.parser")
    sponsorhtml = bill_html.find("th", string="Sponsor:").parent
    billsponsor = sponsorhtml.find('a')
    urlpart = billsponsor['href']
    sponsorid = urlpart.split("/")[-1]
    #sponsorinfo["sponsorpic"] = "https://www.congress.gov/img/member/" + sponsorid.lower() + ".jpg"
    sponsorinfo['sponsorname'] = billsponsor.contents[0]
    memberurl = "https://www.congress.gov" + urlpart
    sponsorinfo["sponsorurl"] = memberurl
    picurlpart = getpic(memberurl)
    sponsorinfo["sponsorpic"] = "https://www.congress.gov" + picurlpart
    return sponsorinfo

# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


@app.route('/')
def showlist():
    client = datastore.Client()
    key = client.key("List", "top_ten")
    mylist = client.get(key)
    res = make_response(mylist)
    res.headers['Content-Type'] = 'application/json; charset=UTF-8'
    res.headers['Access-Control-Allow-Origin'] = '*'
    return res

@app.route('/buildlist')
def scrapebills():
    allweeks = []

    r = requests.get('https://www.congress.gov/most-viewed-bills/')
    cat_html = BeautifulSoup(r.text, "html.parser")

    weeks = cat_html.find_all("table")
    for week in weeks:
        thisweek = {}
        thisweek["bills"] = []
        thisweek["weekname"] = week.find("caption").contents[0]
        billlist = week.find_all("tr")
        for bill in billlist:
            mybill = {}
            if bill.find("td"):
                billfields = bill.find_all("td")
                mybill["rank"] = str(billfields[0].contents[0])
                mybill["billname"] = str(bill.select("a")[0].contents[0])
                mybill["url"] = str(bill.select("a")[0]['href'])
                mybill["billdesc"] = billfields[2].contents[0]
                thisweek["bills"].append(mybill)

        allweeks.append(thisweek)

    latestweek = allweeks[0]
    latestbills = latestweek["bills"]

    countdown = {"bills":[]}

    countdown["week"] = latestweek["weekname"]
    for latestbill in latestbills:
        thisbill = {}
        thisbill["currentrank"] = int(latestbill["rank"][:-1])
        billurl = latestbill["url"]
        m = re.search('([1-9]+)th-congress', billurl)
        nameparts = str(latestbill["billname"]).lower().replace(".","")
        n = re.search('([a-z]+)([1-9]+)', nameparts)
        thisbillcongress = m.group(1)
        thisbillnumber = n.group(2)
        thisbilltype = n.group(1)
        thisbill["title"] = latestbill["billname"] + " [" + thisbillcongress + "th]"
        print(thisbill["title"])
        linkurl = "https://www.govinfo.gov/bulkdata/BILLSTATUS/" + thisbillcongress + "/" + thisbilltype + "/BILLSTATUS-" + thisbillcongress + thisbilltype + thisbillnumber + ".xml"
        #print(thisbill["title"])
        #print(linkurl)
        #print("***")
        #statusinfo = getstatus(linkurl)
        sponsorinfo = getstatus2(str(latestbill["url"]))
        for item in sponsorinfo:
            thisbill[item] = sponsorinfo[item]
        thisbill["url"] = str(latestbill["url"])
        thisbill["billdesc"] = latestbill["billdesc"]
        findlastweek = find(allweeks[1]["bills"],billurl)
        if findlastweek is not None:
            ranklastweek = int(findlastweek["rank"][:-1])
        else:
            ranklastweek = "-"
        thisbill["lastweek"] = ranklastweek
        findtwoweeks = find(allweeks[2]["bills"],billurl)
        if findtwoweeks is not None:
            ranktwoweeks = int(findtwoweeks["rank"][:-1])
        else:
            ranktwoweeks = "-"
        thisbill["twoweeksago"] = ranktwoweeks
        pastranks = []
        for testweek in allweeks:
            testpastweek = find(testweek["bills"],billurl)
            if testpastweek is not None:
                pastranks.append(testpastweek["rank"][:-1])
        print(pastranks)
        thisbill["weeksonchart"] = len(pastranks)
        pastranks.sort()
        print(pastranks)
        thisbill["peak"] = int(pastranks[0])
        countdown["bills"].append(thisbill)
        #print("weeks on chart: " + str(pastcount))

    client = datastore.Client()
    complete_key = client.key("List", "top_ten")
    mylist = datastore.Entity(key=complete_key, exclude_from_indexes=["billlist"])

    now = datetime.now()
    mylist.update(
        {
            "updated": now.strftime("%m/%d/%Y, %H:%M:%S"),
            "billlist": countdown,
        }
    )
    client.put(mylist)
    return countdown


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_app]
# [END gae_python38_app]
