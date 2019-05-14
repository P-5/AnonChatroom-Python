from flask import Flask, render_template, request
import pymysql as sql
import requests
import json
import time



app = Flask(__name__)

# Names come from www.ssa.gov
names = open("names.txt").read().split()
letters = "A B C D E F G H I J K L M N O P Q R S T U V W X Y Z".split()


def date():
  return time.strftime("%Y-%m-%d %H:%M:%S")



def clean(text):
  if text is None:
    return ""
  
  if "CREATE" in text.upper():
    return "SANITIZED"
  if "ALTER" in text.upper():
    return "SANITIZED"
  if "DROP" in text.upper():
    return "SANITIZED"
  if "GRANT" in text.upper():
    return "SANITIZED"
  if "RENAME" in text.upper():
    return "SANITIZED"
  if "REVOKE" in text.upper():
    return "SANITIZED"
  if "SET" in text.upper():
    return "SANITIZED"
  text = text.replace("'", "")
  text = text.replace('"', "")
  
  return text.replace(" ", "_")



def to_html(text):
  return "<center><p>{}</p></center>".format(text)



def to_name(value):
  first = names[value%len(names)]
  middle = letters[value%len(letters)]
  last = letters[int(value/1000)%len(letters)]
  
  return "{} {}. {}.".format(first, middle, last)



def to_comments(comments, post, url):
  comment = open("templates/comment.html").read() 
  
  html = ""
  for i in range(len(comments)):
    html += comment.format(comment=comments[i]["comment"].replace("_", " "), number=comments[i]["number"], score=comments[i]["score"], name=to_name(abs(hash(post + comments[i]["name"]))), url=url)
    #html += comment.format(comment=comments[i]["comment"].replace("_", " "), number=comments[i]["number"], score=comments[i]["score"], name=comments[i]["name"], url=url)
  
  return html



class Memoize:
  def __init__(self, fnc):
    self.args = {}
    self.fnc = fnc
  def __call__(self, *arg):
    if arg not in self.args:
      self.args[arg] = self.fnc(*arg)
    return self.args[arg]



@Memoize
def sentiment(text):
  text = text.replace("_", " ")
  response = requests.post("http://text-processing.com/api/sentiment/", data={"text": text})
  if response is None or response.text is None:
    return ("Sentiment analysis failed.", 0.0)
  data = json.loads(response.text)
  label = data["label"]
  
  print("Sentiment Analysis (Text: {}): {}".format(text, response.text))
  
  return (data["label"], float(data["probability"][label]))



@app.route("/")
def home():
  return render_template("home.html")



@app.route("/tables")
def tables():
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  cursor.execute("SHOW TABLES")
  tables = cursor.fetchall()
  
  connection.close()
  
  if len(tables) == 0:
    return to_html("Tables: ")
  
  text = "</p><p>"
  for i in range(len(tables)):
    for key in tables[i]:
      text += str(tables[i][key]) + "</p><p>"
  return to_html("Tables: {}".format(text))



@app.route("/users")
def users():
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  cursor.execute("SELECT * FROM users")
  users = cursor.fetchall()
  
  connection.close()
  
  if len(users) == 0:
    return to_html("Users: ")
  
  text = "</p><p>"
  for i in range(len(users)):
    for key in users[i]:
      text += str(key) + ": " + str(users[i][key]) + " "
    text += "</p><p>"
  return to_html("Users: {}".format(text))



@app.route("/signup")
def signup_form():
  name = request.args.get("delete")
  
  if not name is None:
    connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
    cursor = connection.cursor(sql.cursors.DictCursor)
    
    cursor.execute("DELETE * FROM users WHERE name='{}'".format(name))
    connection.commit()
  
  return render_template("signup_form.html")



@app.route("/signup", methods=["POST"])
def signup():
  name = request.form["name"]
  name = clean(name)
  
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  cursor.execute("SELECT * FROM users WHERE name='{}'".format(name))
  user = cursor.fetchall()
  
  if len(user) == 0:
    cursor.execute("INSERT INTO users SET name='{}'".format(name))
    connection.commit()
    
    cursor.execute("SELECT * FROM users WHERE name='{}'".format(name))
    user = cursor.fetchall()
  
  forums = ""
  cursor.execute("SHOW TABLES")
  tables = cursor.fetchall()
  
  for i in range(len(tables)):
    for key in tables[i]:
      if tables[i][key].startswith("post_"):
        cursor.execute("SELECT * FROM {} WHERE name='{}'".format(tables[i][key], name))
        comments = cursor.fetchall()
        count = 0.0
        pos = 0.0
        neg = 0.0
        posVal = 0.0
        negVal = 0.0
        for j in range(len(comments)):
          label, val = sentiment(comments[j]["comment"])
          if label == "pos":
            posVal += val
            pos += 1
          if label == "neg":
            negVal += val
            neg += 1
          count += 1
        suffix = " (N/A)"
        if 0 < count:
          suffix = " ({}% Pos / {}% Neg)".format(round(100 * pos / count, 2), round(100 * neg / count, 2))
        forums += "<a href='post?user={0}&post={1}'><b>{1}</b>{2}</a><br>".format(name, tables[i][key][5:], suffix)
  forums += "<br>"
  
  connection.close()
  
  html = open("templates/signup.html").read()
  return html.format(name=user[0]["name"], posts=user[0]["posts"], comments=user[0]["comments"], upvotes=user[0]["upvotes"], downvotes=user[0]["downvotes"], forums=forums)




@app.route("/post")
def post_form():
  name_user = request.args.get("user")
  name_post = request.args.get("post")
  if name_user is None or name_post is None:
    return render_template("post_form.html")
  name_user = clean(name_user)
  name_post = clean(name_post)
  
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  cursor.execute("SELECT * FROM post_{} ORDER BY number DESC LIMIT 100".format(name_post))
  comments = cursor.fetchall()
  
  upvote = request.args.get("upvote")
  downvote = request.args.get("downvote")
  if upvote is not None:
    upvote = clean(upvote)
    cursor.execute("UPDATE users SET upvotes=upvotes+1 WHERE name=(SELECT name FROM post_{} WHERE number='{}')".format(name_post, upvote))
    cursor.execute("UPDATE post_{} SET score=score+1 WHERE number='{}'".format(name_post, upvote))
    connection.commit()
  if downvote is not None:
    downvote = clean(downvote)
    cursor.execute("UPDATE users SET downvotes=downvotes-1 WHERE name=(SELECT name FROM post_{} WHERE number='{}')".format(name_post, downvote))
    cursor.execute("UPDATE post_{} SET score=score-1 WHERE number='{}'".format(name_post, downvote))
    connection.commit()
  if upvote is not None or downvote is not None:
    cursor.execute("SELECT * FROM post_{} ORDER BY number DESC LIMIT 100".format(name_post))
    comments = cursor.fetchall()
  
  connection.close()
  
  html = open("templates/post.html").read()
  url = "/post?user={}&post={}".format(name_user, name_post)
  return html.format(comments=to_comments(comments, name_post, url))



@app.route("/post", methods=["POST"])
def post():
  name_user = request.args.get("user")
  name_post = request.args.get("post")
  if name_post is None:
    if "name" in request.form:
      name_post = request.form["name"]
      bots = request.form["bots"]
      bots = clean(bots)
    else:
      return to_html("Post created.")
  name_user = clean(name_user)
  name_post = clean(name_post)
  
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  if "comment" in request.form:
    comment = request.form["comment"]
    comment = clean(comment)
    cursor.execute("INSERT INTO post_{} SET comment='{}', name='{}'".format(name_post, comment, name_user))
    cursor.execute("UPDATE users SET comments=comments+1 WHERE name='{}'".format(name_user))
    connection.commit()
  elif not "filter" in request.form:
    cursor.execute("CREATE TABLE IF NOT EXISTS post_{} (comment TEXT NOT NULL, name TEXT NOT NULL, score INT DEFAULT 0, number INT AUTO_INCREMENT, PRIMARY KEY ( number ))".format(name_post))
    cursor.execute("UPDATE users SET posts=posts+1 WHERE name='{}'".format(name_user))
    connection.commit()
    bots = bots.split()
    for i in range(len(bots)):
      other_post = bots[i].split(":")[0]
      pattern = bots[i].split(":")[1]
      message = bots[i].split(":")[2].replace("_", " ")
      cursor.execute("CREATE TRIGGER post_{}_{} AFTER INSERT ON post_{} FOR EACH ROW BEGIN IF NEW.comment LIKE '{}' THEN INSERT INTO post_{} SET comment=CONCAT('{}', ' (Triggered by: ', NEW.comment, ')'), name='Bot'; END IF; END".format(name_post, i, other_post, pattern, name_post, message))
    connection.commit()
    connection.close()
    
    return to_html("Post created.");
  
  where = ""
  if "filter" in request.form:
    filters = request.form["filter"].split()
    if not filters is None and len(filters) != 0:
      for query in filters:
        subquery = query.split(":")
        if len(subquery) == 2 and subquery[0] == "globalUpvotes":
          where = " LEFT JOIN users ON post_{}.name = users.name WHERE upvotes >= {}".format(name_post, int(subquery[1]))
        elif len(subquery) == 2 and subquery[0] == "globalDownvotes":
          where = " LEFT JOIN users ON post_{}.name = users.name WHERE downvotes <= {}".format(name_post, -int(subquery[1]))
        else:
          if where == "":
            where = " WHERE "
          else:
            where += " AND "
          where += "comment LIKE '%{}%'".format(clean(query.replace("_", " ")))
  
  cursor.execute("SELECT * FROM post_{}{} ORDER BY number DESC LIMIT 100".format(name_post, where))
  comments = cursor.fetchall()
  
  connection.close()
  
  html = open("templates/post.html").read()
  url = "/post?user={}&post={}".format(name_user, name_post)
  return html.format(comments=to_comments(comments, name_post, url))



if __name__ == "__main__":
  app.run(host="0.0.0.0")
