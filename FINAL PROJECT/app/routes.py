from flask import flash, redirect, render_template, url_for, request
from app.forms import LoginForm, RegistrationForm, UpdateForm, BookForm
from app.models import User, Book, CartItem
from app import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
import os
# import requests


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
   return render_template('home.html')

@app.route('/sign-in',  methods=['POST', 'GET'])
def sign_in():
   if current_user.is_authenticated:
      return redirect(url_for('home'))
   form = LoginForm()
   if form.validate_on_submit():
      user = User.query.filter_by(email = form.email.data).first()
      if user and bcrypt.check_password_hash(user.password, form.password.data):
         login_user(user, remember=form.remember.data)
         next_page = request.args.get('next')
         return redirect(next_page) if next_page else redirect(url_for('home'))
      else:
         flash('Login unsuccessful! Please check the email and password!', 'danger')
   return render_template('sign-in.html', title='Sign-in', form=form)

@app.route('/sign-up', methods=['POST', 'GET'])
def sign_up():
   if current_user.is_authenticated:
      return redirect(url_for('home'))
   form = RegistrationForm()
   if form.validate_on_submit():
      hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
      data = {
         "username": form.username.data,
         "first_name": form.first_name.data,
         "last_name": form.last_name.data,
         "email": form.email.data,
         "password": hashed_password
      }

      # response = requests.post("http://127.0.0.1:8000/create_user", json=data)

      user = User(username = form.username.data, 
                           first_name = form.first_name.data, 
                           last_name = form.last_name.data, 
                           email = form.email.data, 
                           password = hashed_password)
      db.session.add(user)
      db.session.commit()
      flash(f'Your account has been created! You are now able to log in!', 'success')
      return redirect(url_for('sign_in'))
   
   return render_template('sign-up.html', title='Sign-up', form=form)
@app.route("/logout")
def logout():
   logout_user()
   return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
   image_file = url_for('static', filename='img/' + current_user.image_file)
   return render_template('account.html', title = 'Account', image_file = image_file)

@app.route("/account-update", methods=['POST', 'GET'])
@login_required
def account_update():
   form = UpdateForm()
   image_file = url_for('static', filename='img/' + current_user.image_file)
   if request.method == "GET":
      form.username.data = current_user.username
      form.first_name.data = current_user.first_name
      form.last_name.data = current_user.last_name
      form.phone_number.data = current_user.phone_number
      form.address.data = current_user.address
      form.email.data = current_user.email
      return render_template('account-update.html', title = 'Account', image_file = image_file, form = form)
   elif request.method == "POST":
      if form.validate_on_submit:
         current_user.username = form.username.data
         current_user.first_name = form.first_name.data
         current_user.last_name = form.last_name.data
         current_user.phone_number = form.phone_number.data
         current_user.address = form.address.data
         current_user.email = form.email.data
         db.session.commit()  
         flash("Your account has been updated!", 'success')
         return redirect(url_for('account'))
      
@app.route('/users')
@login_required
def users():
   users = User.query.all()
   image_file = url_for('static', filename='img/' + current_user.image_file)
   return render_template('users.html', users = users, image_file = image_file)

@app.route('/user_page/<user_id>', methods = ['GET', 'POST'])
@login_required
def user_page(user_id):
    current_user = db.session.query(User).filter(User.id==user_id).first()
    image_file = url_for('static', filename='img/' + current_user.image_file)
    return render_template("user_page.html", user=current_user, image_file = image_file)

@app.route("/books")
def books():
    books = Book.query.all()
    return render_template('books.html', books=books)

@app.route("/books/<int:book_id>")
def book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book.html', book=book)

@app.route("/books/new", methods=['GET', 'POST'])
def new_book():
    form = BookForm()
    if form.validate_on_submit():
        file = form.image.data
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            book = Book(
                  name=form.name.data,
                  author=form.author.data,
                  price=form.price.data,
                  description=form.description.data,
                  image = filename
            )
        db.session.add(book)
        db.session.commit()
        flash('Your book has been created!', 'success')
        return redirect(url_for('books'))
    return render_template('create_book.html', title='New Book', form=form)

@app.route("/books/<int:book_id>/edit", methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    form = BookForm()
    if form.validate_on_submit():
        book.name = form.name.data
        book.author = form.author.data
        book.price = form.price.data
        book.description = form.description.data
        db.session.commit()
        flash('Your book has been updated!', 'success')
        return redirect(url_for('book', book_id=book.id))
    elif request.method == 'GET':
        form.name.data = book.name
        form.author.data = book.author
        form.price.data = book.price
        form.description.data = book.description
    return render_template('create_book.html', title='Edit Book', form=form)

@app.route("/books/<int:book_id>/delete", methods=['POST'])
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Your book has been deleted!', 'success')
    return redirect(url_for('books'))

@app.route('/add_to_cart/<int:book_id>')
@login_required
def add_to_cart(book_id):
    book = Book.query.get_or_404(book_id)
    cart_item = CartItem(user=current_user, book=book)
    db.session.add(cart_item)
    db.session.commit()
    flash('Item added to your cart!', 'success')
    return redirect(url_for('home'))

@app.route('/cart')
@login_required
def cart():
    cart_items = current_user.cart_items
    total_price = sum(item.book.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove_from_cart/<int:item_id>', methods=['GET', 'POST'])
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    if cart_item.user != current_user:
        flash('Permission denied. This item does not belong to you.', 'danger')
        return redirect(url_for('cart'))
    db.session.delete(cart_item)
    db.session.commit()
    flash('Item removed from your cart.', 'success')
    return redirect(url_for('cart'))
