import pymysql as sql
import json
import csv



def unparse(text):
  return " ".join(text.replace(" nt", "nt").replace(" s ", "s ").strip().split())


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



def signup(name):
  name = clean(name)
  
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  cursor.execute("SELECT * FROM users WHERE name='{}'".format(name))
  user = cursor.fetchall()
  
  if len(user) == 0:
    cursor.execute("INSERT INTO users SET name='{}'".format(name))
    connection.commit()
  
  connection.close()



def vote(name_user, name_post, index, magnitude):
  name_user = clean(name_user)
  name_post = clean(name_post)
  
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  upvote = None
  downvote = None
  if 0 < magnitude:
    upvote = index
  else:
    downvote = index
  if upvote is not None:
    cursor.execute("UPDATE users SET upvotes=upvotes+{} WHERE name='{}'".format(magnitude, name_user))
    cursor.execute("UPDATE post_{} SET score='{}' WHERE number='{}'".format(name_post, magnitude, upvote))
    connection.commit()
  if downvote is not None:
    cursor.execute("UPDATE users SET downvotes=downvotes+{} WHERE name='{}'".format(magnitude, name_user))
    cursor.execute("UPDATE post_{} SET score='{}' WHERE number='{}'".format(name_post, magnitude, downvote))
    connection.commit()
  
  connection.close()



def post(name_user, name_post, comment):
  name_user = clean(name_user)
  name_post = clean(name_post)
  comment = clean(comment)
  
  connection = sql.connect(host="localhost", user="root", password="", database="rootDB")
  cursor = connection.cursor(sql.cursors.DictCursor)
  
  cursor.execute("CREATE TABLE IF NOT EXISTS post_{} (comment TEXT NOT NULL, name TEXT NOT NULL, score INT DEFAULT 0, number INT AUTO_INCREMENT, PRIMARY KEY ( number ))".format(name_post))
  connection.commit()
  
  cursor.execute("INSERT INTO post_{} SET comment='{}', name='{}'".format(name_post, comment, name_user))
  cursor.execute("UPDATE users SET comments=comments+1 WHERE name='{}'".format(name_user))
  connection.commit()
  
  connection.close()



with open("reddit-dataset/learning_todayilearned.csv", "rb") as csvFile:
  spamReader = csv.reader(csvFile)
  commentsRead = 0

  for row in spamReader:
    if len(row) < 12 or len(row[1]) < 5:
      continue
    #if 50 < commentsRead:
      #break
    commentsRead += 1
    #print("Post: {}".format(row[3]))
    #print("User: {}".format(row[6]))
    #print("Text: {}".format(unparse(row[1])))
    #print("Ups: {}".format(int(float(row[7]))))
    #print("Downs: {}".format(int(float(row[8]))))
    #print("\n")
    i = commentsRead
    p = row[3]
    u = row[6]
    t = unparse(row[1])
    uv = int(float(row[7]))
    dv = int(float(row[8]))
    # Since our dataset doesn't count downvotes
    v = uv
    signup(u)
    post(u, p, t)
    vote(u, p, i, v)
    if commentsRead % 100 == 0:
      print("{} comments have been parsed.".format(commentsRead))
