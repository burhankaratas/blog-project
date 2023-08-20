from flask import Flask,render_template,flash,redirect,url_for,session,logging,request,g
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators, SubmitField
from passlib.hash import sha256_crypt 
from functools import wraps


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntüleme izniniz yok", "danger")
            return redirect(url_for("index"))
    return decorated_function
 
# Kullanıcı Kayıt Formu
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min = 4,max = 25),])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min = 5,max = 35),])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Giriniz...")])
    password = PasswordField("Parola:",validators=[validators.DataRequired(message = "Lütfen Bir Parola Belirleyiniz"),
      validators.EqualTo(fieldname = "confirm",message="Parolanız Uyuşmuyor...")
 
    ])
    confirm = PasswordField("Parola Doğrula")
 
 
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")



# Katılım Formu

class BizeKatilinForm(Form):
    name = StringField("İsim Soyisim", validators=[validators.length(min=3, max=35)])
    email = StringField("Email Adresi", validators=[validators.Email()])
    phoneNumber = StringField("Telefon Numaranız") 
    content = TextAreaField("Ekibimize Neden Katılmak İstiyorsunuz?")
 
app = Flask(__name__)
app.secret_key= "yeblog"
 
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "yeblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


 
 
mysql = MySQL(app)
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hakkimizda")
def about():
  return render_template("about.html")


@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")       
    



@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html", articles = articles)
    else:
        return render_template("articles.html")
    

@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * From articles where id = %s"


    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")


 
#Kayıt Olma
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
 
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt (form.password.data)
 
 
        cursor = mysql.connection.cursor()
 
        sorgu = "INSERT INTO users(name,email,username,password) VALUES(%s,%s,%s,%s)"
 
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
 
        cursor.close
        flash("Başarıyla Kayıt Oldunuz...","success")
 
        return redirect(url_for("login"))
 
    else:
        return render_template("register.html",form = form)



#Giriş İşlemi
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)

    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * From users where username = %s"

        result = cursor.execute(sorgu, (username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if sha256_crypt.verify(password_entered, real_password):
                flash("Başarıyla giriş yaptınız!", "success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanız Yanlış.", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunamadı.", "danger")
            return redirect(url_for("login"))


    return render_template("login.html", form = form)


@app.route("/logout")
def logout():
    session.clear()
    flash("Başarıyla çıkış yaptınız.", "success")
    return redirect(url_for("login"))


# Makale Ekleme

@app.route("/addarticle", methods = ["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title, author, content) VALUES(%s, %s, %s)"

        cursor.execute(sorgu,(title, session["username"], content))

        mysql.connection.commit()

        cursor.close()


        flash("Makale başarıyla eklendi.", "success")
        return redirect(url_for("dashboard"))
    
    return render_template("addarticle.html", form = form)


# Makale Güncelleme

@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id, session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok", "danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()

            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]

            return render_template("update.html", form = form)
    else:
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle, newContent, id))

        mysql.connection.commit()

        flash("Makale Başarıyla güncellendi", "success")

        return redirect(url_for("dashboard"))

# Makale Silme

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()


    sorgu = "Select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"], id))

    if result > 0:
        sorgu2 = "Delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else:
        flash("Makaleyi silme yetkiniz yok veya böyle bir makale yok.", "danger")
        return redirect(url_for("index"))


# Katılım Form Sayfası 

@app.route("/bizekatilin",methods = ["GET","POST"])
def bizekatil():
    form = BizeKatilinForm(request.form)
 
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        phone = form.phoneNumber.data
        content = form.content.data
 
 
        cursor = mysql.connection.cursor()
 
        sorgu = "INSERT INTO bizekatilin(name,mail,phone,content) VALUES(%s,%s,%s,%s)"
 
        cursor.execute(sorgu,(name,email,phone,content))
        mysql.connection.commit()
 
        cursor.close()
        flash("Formunuz Başarıyla Gönderildi..","success")
 
        return redirect(url_for("index"))
 
    else:
        return render_template("bizekatilin.html",form = form)
    


    




# Makale Form

class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.length(min=3, max=50)])
    content = TextAreaField("İçerik", validators=[validators.length(min=10)])





if __name__ == "__main__":
    app.run(debug= True)
 