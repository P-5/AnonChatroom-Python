import urllib.request
import json
import time

urls = ["https://www.reddit.com/r/UIUC/new/.json?limit=100"]

after = ""
posts = []
for i in range(10):
  time.sleep(1)
  print("Requesting posts....")
  url = urls[0] + after
  request = urllib.request.Request(url, headers={"User-agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64)"})
  with urllib.request.urlopen(request) as site:
    data = json.loads(site.read().decode())
    for post in data["data"]["children"]:
      posts.append("https://www.reddit.com"+post["data"]["permalink"])
    if data["data"]["after"] is None:
      break
    after = "&after="+data["data"]["after"]

scrape = []
for url in posts:
  time.sleep(1)
  try:
    print("Requesting post....")
    request = urllib.request.Request(url+".json", headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; Win64; x64)"})
    with urllib.request.urlopen(request) as site:
      data = json.loads(site.read().decode())
      scrape.append(data)
  except Exception as e:
    print("Exception {}".format(e))
    print("Url {}".format(url+".json"))
    break
with open("scrape.json", "w") as out:
  json.dump(scrape, out)
print("Scraped {} posts".format(len(scrape)))
