from flask import Flask, render_template, redirect, request, session, flash
from flask_bcrypt import Bcrypt
from mysqlconnection import connectToMySQL
import re

app = Flask(__name__)
app.secret_key = "secret"
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
bcrypt = Bcrypt(app)

@app.route('/')
def index():
	if 'logged_id' in session.keys():
		if session['logged_id'] == 'logout':
			if 'logged_first' in session.keys():
				first = session['logged_first']
				last = session['logged_last']
				session.clear()
				flash(f"Goodbye, "+first+" "+last,'log_out')
				return redirect('/')
			session.clear()
			flash("How did that happen", 'log_out')
			return redirect('/')
		session.clear()
		flash("I took the liberty of logging you out", 'log_out')
		return redirect('/')
	return render_template('index.html')

@app.route('/register',methods=['post'])
def register():
	session['first_name'] = request.form['first_name']
	session['last_name'] = request.form['last_name']
	session['email'] = request.form['email']
	if len(request.form['first_name']) < 1:
		flash("Don't leave blank","first_name")
	if len(request.form['last_name']) < 1:
		flash("Don't leave blank","last_name")
	if not EMAIL_REGEX.match(request.form['email']):
		flash("Invalid email!",'email')
	if len(request.form['password']) < 8:
		flash("Password must be more than 8 characters","password")
	if request.form['password'] != request.form['pass_confirm']:
		flash("passwords do not match", 'password-confirm')
	if not EMAIL_REGEX.match(request.form['email']):
		flash("Invalid email address!", 'email')
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db("SELECT * FROM users")
	for user in result:
		if user['email'] == request.form['email']:
			flash("Email is taken",'email')
	if '_flashes' in session.keys():
		return redirect('/')
	pw_hash = bcrypt.generate_password_hash(request.form['password'])
	data = {
		'first': request.form['first_name'],
		'last': request.form['last_name'],
		'email': request.form['email'],
		'pass': pw_hash
	}
	query = "INSERT INTO users (first_name, last_name, email, password, created_at) VALUES (%(first)s,%(last)s,%(email)s,%(pass)s, NOW())"
	mysql = connectToMySQL('favorite_books')
	new_user = mysql.query_db(query,data)
	data = {'id_new': new_user}
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db("SELECT * from users WHERE id = '%(id_new)s' ",data)
	session['logged_id'] = result[0]['id']
	session['logged_first'] = result[0]['first_name']
	session['logged_last'] = result[0]['last_name']
	print("New user:",new_user)
	print(session)
	return redirect('/main')

@app.route('/login',methods=['post'])
def login():
	debugHelp("*** LOG IN ***")
	session['email_login'] = request.form['email_login']
	log_mail = request.form['email_login']
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db("SELECT * FROM users")
	if result != False:
		for user in result:
			print("result: ",result)
			print("user: ",user)
			if len(request.form['email_login']) < 1:
				flash("Field is empty, like my soul ",'email_login')
				return redirect('/')
			if user['email'] == log_mail:
				if bcrypt.check_password_hash(user['password'], request.form['password_login']):
					session['logged_id'] = user['id']
					session['logged_first'] = user['first_name']
					session['logged_last'] = user['last_name']
					return redirect('/main')
				flash("Password does not match",'password_login')
				return redirect('/')
		flash("No matching e-mail address", 'password_login')
		return redirect('/')
	flash("No users yet", 'log_out')
	debugHelp("*** /LOG IN ***")
	return redirect('/')

@app.route('/logout')
def logout():
	session['logged_id'] = 'logout'
	return redirect('/')

@app.route('/main')
def main():
	print("*\n*"*20+"          MAIN        "+"*\n*"*20)
	if 'logged_id' in session.keys() and session['logged_id'] != 'logout':
		user_id = session['logged_id']
		full_name = session['logged_first']+" "+session['logged_last']
		# mysql = connectToMySQL('favorite_books')
		# result = mysql.query_db("SELECT * FROM books")
		mysql = connectToMySQL('favorite_books')
		result2 = mysql.query_db("SELECT * FROM books JOIN users ON users.id = books.uploaded_by_id")
		print(result2)
		print("************* Logged user ID:",user_id)
		print("session:",session)
		flash(full_name,'welcome')
		print("*\n*"*20+"          MAIN        "+"*\n*"*20)
		return render_template('main.html',user_id=user_id,full_name=full_name,data2=result2)
	flash("Unauthorized", 'log_out')
	print("*\n*"*20+"          MAIN        "+"*\n*"*20)
	return redirect('/')


@app.route('/add_book',methods=['post'])
def add_book():
	data = {
		'id': request.form['uploader_id'],
		'title': request.form['title'],
		'author': request.form['author'],
		'description': request.form['description'],
	}
	query = "INSERT INTO books (uploaded_by_id, title, author, description, created_at) VALUES (%(id)s, %(title)s, %(author)s,%(description)s, NOW())"
	mysql = connectToMySQL('favorite_books')
	new_book_id = mysql.query_db(query,data)
	uploader_id = request.form['uploader_id']
	print("New book ID:", new_book_id)
	book_to_fav_id = new_book_id
	mysql = connectToMySQL('favorite_books')
	users_who_fav_this_book = mysql.query_db("SELECT * from books join favorites on favorites.book_id = books.id join users on users.id = favorites.user_id WHERE books.id = %(id)s;",{'id':book_to_fav_id})
	for user in users_who_fav_this_book:
		print("\n************","Faved User ID:",user['users.id'],"*****************\n")
		if int(user_id) == int(user['users.id']):
			print("USER ID:",user_id)
			print("user['users.id']:", user['users.id'])
			print("That's weird")
			flash("Already added", 'favorite')
			return redirect('/main')
	data = {
		'book_id': book_to_fav_id,
		'user_id': uploader_id,
	}
	query = "INSERT INTO favorites (user_id, book_id,created_at) VALUES (%(user_id)s,%(book_id)s,NOW());"
	mysql = connectToMySQL('favorite_books')
	new_fav_id = mysql.query_db(query,data)
	print(new_fav_id)
	return redirect('/main')

@app.route('/view_book/<x>/<y>')
def view_book(x,y):
	debugHelp("*** VIEW BOOK ***")
	book_id = x
	user_id = int(y)
	data = {
		'id':book_id,
	}
	mysql = connectToMySQL('favorite_books')
	book = mysql.query_db("SELECT * FROM books JOIN users on books.uploaded_by_id = users.id WHERE books.id = %(id)s",data)
	uploader_id = int(book[0]['uploaded_by_id'])
	uploader_full_name = book[0]['first_name'] +" "+ book[0]['last_name']
	print("book:",book)
	print("user_id:",user_id)
	print("uploader_id:",uploader_id)
	data = {
		'book_id': book_id,
	}
	query = "SELECT * from books join favorites on favorites.book_id = books.id join users on users.id = favorites.user_id WHERE books.id = %(book_id)s;"
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db(query,data)
	print("\nRESULT:",result,"\n")
	full_name = session['logged_first']+" "+session['logged_last']
	user_likes = False
	for fav in result:
		if fav['user_id'] == user_id:
			user_likes = True
	debugHelp("*** /VIEW BOOK ***")
	return render_template('view_book.html',user_likes=user_likes,book=book,book_id=book_id,user_id=user_id,uploader_id=uploader_id, uploader_full_name=uploader_full_name, data=result,full_name=full_name)

@app.route('/delete_book/<x>')

def delete_book(x):

	debugHelp("*** DELETE BOOK ***")
	print("Book ID to delete:",x)
	data = {
		'id':x,
	}
	query = "SELECT * FROM books join favorites on favorites.book_id = books.id join users on users.id = favorites.user_id WHERE books.id = %(id)s"
	mysql = connectToMySQL('favorite_books')
	book_to_delete = mysql.query_db(query,data)
	print("Book to delete:",book_to_delete)
	print("uploader\'s_id ",book_to_delete[0]['uploaded_by_id'])
	if book_to_delete[0]['uploaded_by_id'] == session['logged_id']:
		if book_to_delete[0]['favorites.id']:
			mysql = connectToMySQL('favorite_books')
			mysql.query_db("DELETE from favorites WHERE book_id = %(id)s", data)
		print("DESTROY",book_to_delete[0]['uploaded_by_id'])
		data = {
			'id': x,
		}
		query = "DELETE FROM books WHERE books.id = %(id)s"
		mysql = connectToMySQL('favorite_books')
		delete_result = mysql.query_db(query,data)
		print("Result:", delete_result)
	else:
		print("You don't get to do that")
		# flash("not yours to delete",'delete_book')
	debugHelp("*** /DELETE BOOK ***")
	return redirect('/main')


@app.route('/edit_book/<x>', methods=['post'])
def edit_book(x):
	debugHelp("EDIT BABY")
	print("request form:",request.form)
	book_to_edit_id = x
	data = {
		'id': book_to_edit_id,
		'title': request.form['title'],
		'author': request.form['author'],
		'dscp': request.form['description'],
	}
	query = "UPDATE books SET title=%(title)s, author=%(author)s, description=%(dscp)s, updated_at=NOW() WHERE books.id = %(id)s"
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db(query,data)
	print(result)
	debugHelp("EDIT BABY")
	return redirect('/main')


@app.route('/favorite_book/<x>/<y>')
def favorite_book(x,y):
	debugHelp("*** FAVORITE  ***")
	book_to_fav_id = x
	user_id = y
	mysql = connectToMySQL('favorite_books')
	users_who_fav_this_book = mysql.query_db("SELECT * from books join favorites on favorites.book_id = books.id join users on users.id = favorites.user_id WHERE books.id = %(id)s;",{'id':book_to_fav_id})
	for user in users_who_fav_this_book:
		print("\n************","Faved User ID:",user['users.id'],"*****************\n")
		if int(user_id) == int(user['users.id']):
			print("USER ID:",user_id)
			print("user['users.id']:", user['users.id'])
			print("Yo, you already faved this.  I get it.")
			flash("Already added", 'favorite')
			return redirect('/main')
	data = {
		'book_id': book_to_fav_id,
		'user_id': user_id,
	}
	query = "INSERT INTO favorites (user_id, book_id,created_at) VALUES (%(user_id)s,%(book_id)s,NOW());"
	mysql = connectToMySQL('favorite_books')
	new_fav_id = mysql.query_db(query,data)
	print("New fav ID:", new_fav_id)
	debugHelp("*** /FAVORITE BOOK ***")
	return redirect(f'/view_book/{book_to_fav_id}/{user_id}')


@app.route('/unfavorite_book/<x>/<y>')
def unfavorite_book(x,y):
	data = {
	'favorite_id': int(x)
	}
	query = "DELETE FROM favorites WHERE id = %(favorite_id)s"
	mysql = connectToMySQL('favorite_books')
	delete_result = mysql.query_db(query,data)
	user_id = session['logged_id']
	print("Result:", delete_result)
	return redirect(f'/view_book/{int(y)}/{user_id}')

@app.route('/edit_user/')
def edit_user():
	user_id = session['logged_id']
	return render_template('edit_user.html',id_edit=user_id)

@app.route('/process_edit_user',methods=['post'])
def process_edit_user():
	debugHelp("*** PROCESS EDIT USER ***")
	session['first_name'] = request.form['first_name']
	session['last_name'] = request.form['last_name']
	session['email'] = request.form['email']
	if len(request.form['first_name']) < 1:
		flash("Name must be at least 1 character", 'first_name')
	if len(request.form['last_name']) < 1:
		flash("Name must be at least 1 character", 'last_name')
	if request.form['first_name'].isalpha() == False:
		flash("Name must not contain any numbers, spaces, or funky letters", 'first_name')
	if request.form['last_name'].isalpha() == False:
		flash("Name must not contain any numbers, spaces, or funky letters", 'last_name')
	if not EMAIL_REGEX.match(request.form['email']):
		flash("Invalid email address!", 'email')
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db("SELECT * FROM users")
	for user in result:
		if user['email'] == request.form['email']:
			flash("Hey, stupid, that e-mail is taken.  You are not special.",'email')
	if len(request.form['password']) < 8:
		flash("Password must be more than 8 characters", 'password')
	if request.form['password'] != request.form['password_confirm']:
		flash("Passwords must match", 'password_confirm')
	if '_flashes' in session.keys():
		x = request.form['id_to_edit']
		return redirect('/edit_user')
	pw_hash = bcrypt.generate_password_hash(request.form['password'])
	data = {
		'id': request.form['id_to_edit'],
		'first': request.form['first_name'],
		'last': request.form['last_name'],
		'email': request.form['email'],
		'pw_hash': pw_hash,
	}
	query = "UPDATE users SET first_name=%(first)s, last_name=%(last)s, email=%(email)s, password=%(pw_hash)s, updated_at=NOW() WHERE id = %(id)s"
	mysql = connectToMySQL('favorite_books')
	edited_user_id = mysql.query_db(query,data)
	print("edited_user_id:", edited_user_id)
	mysql = connectToMySQL('favorite_books')
	result = mysql.query_db("SELECT * from users WHERE id = %(id)s ",{'id': session['logged_id']})
	session['logged_first'] = result[0]['first_name']
	session['logged_last'] = result[0]['last_name']
	debugHelp("*** /PROCESS EDIT USER ***")
	return redirect('/main')

@app.route('/delete_user/<x>')
def delete_user(x):
	return redirect('/main')

def debugHelp(message = ""):
	print("\n\n--------------------", message, "--------------------")
	print('REQUEST.FORM:', request.form)
	print('SESSION:', session)

if __name__=="__main__":
	app.run(debug=True)
































