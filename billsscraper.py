from bs4 import BeautifulSoup
import requests

def find(arr, namestr):
    for x in arr:
        if x["url"] == namestr:
            return x

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
            mybill["rank"] = billfields[0].contents[0]
            mybill["billname"] = bill.select("a")[0].contents[0]
            mybill["url"] = bill.select("a")[0]['href']
            mybill["billdesc"] = billfields[2].contents[0]
            thisweek["bills"].append(mybill)

    allweeks.append(thisweek)

latestweek = allweeks[0]
latestbills = latestweek["bills"]

print(latestweek["weekname"])
for bill in latestbills:
    currentrank = bill["rank"]
    billname = bill["billname"]
    billurl = bill["url"]
    billdesc = bill["billdesc"]
    findlastweek = find(allweeks[1]["bills"],billurl)
    if findlastweek is not None:
        ranklastweek = findlastweek["rank"]
    else:
        ranklastweek = "-"
    findtwoweeks = find(allweeks[2]["bills"],billurl)
    if findtwoweeks is not None:
        ranktwoweeks = findtwoweeks["rank"]
    else:
        ranktwoweeks = "-"
    print(billname)
    print("this week: " + currentrank)
    print("last week: " + ranklastweek)
    print("two weeks ago: " + ranktwoweeks)
    pastcount = 0
    for testweek in allweeks:
        testpastweek = find(testweek["bills"],billurl)
        if testpastweek is not None:
            pastcount = pastcount+1
    print("weeks on chart: " + str(pastcount))
