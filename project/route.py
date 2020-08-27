from flask import render_template, request, flash, redirect, url_for, abort
from project import app, db, parameters, mail, bcrypt
from project.connection import Post, Comment, User
from project.forms import (RegistrationForm, LoginForm, EditAccountForm, Postsubmitform,
                           Postupdateform, RequestPasswordResetForm, PasswordResetForm)
from flask_login import login_user, current_user, logout_user, login_required
from project.forms import save_pic
from datetime import datetime
from sqlalchemy import desc


@app.route('/')
@app.route('/home')
def home():
    # posts_= Post.query.order_by(desc(Post.date)).limit(parameters['no_of_post_in_Homepage']).all()->without pagination
    # pagination
    page = request.args.get('page', 1, type=int)  # ref:login route, default value =1
    # no one can enter a value other than int which will raise an error
    posts_ = Post.query.order_by(desc(Post.date)).paginate(page=page, per_page=parameters['no_of_post_in_Homepage'])
    return render_template('home.html', title='Home', user=current_user, parameter=parameters, posts=posts_,
                           show_navbar=True)


@app.route('/registration', methods=["GET", "POST"])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  # password encryption
        if form.picture.data:
            pic_name = save_pic(form.picture.data, 'registration')
        else:
            pic_name = 'default_pic.png'
        user = User(name=form.username.data,
                    password=hashed_password,
                    email=form.email.data,
                    image_file=pic_name,
                    role='author')
        db.session.add(user)
        db.session.commit()
        flash(f'Account Successfully created for {form.username.data} successfully.', 'success')
        return redirect(url_for('home'))
    return render_template('registration.html', parameter=parameters, title='Registration Form', show_navbar=False,
                           form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash("You are logged in successfully", 'success')
            redirecting_page = request.args.get('next')  # getting the value of next from the Url query
            return redirect(redirecting_page) if redirecting_page else redirect(url_for('home'))
        else:
            flash("Login failed. Check Email and Password again", 'danger')
    return render_template('login.html', parameter=parameters, title='Login Form', form=form, show_navbar=False)


@app.route('/account', methods=["GET", "POST"])
@login_required
def account():
    form = EditAccountForm()
    if form.validate_on_submit():
        current_user.name = form.username.data
        current_user.email = form.email.data
        if form.picture.data:
            pic_name = save_pic(form.picture.data, 'modify')  # save picture and return the name
            current_user.image_file = pic_name
        db.session.commit()
        flash("Your account has been updated.", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.name  # showing the current name
        form.email.data = current_user.email  # showing the current email address

    image = url_for('static', filename='img/profile_pics/' + current_user.image_file)  # showing the image in account
    return render_template('account.html', parameter=parameters, curr_name=current_user.name,
                           curr_email=current_user.email, image=image, form=form, title='Account',
                           show_navbar=False)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first_or_404()
        send_reset_mail(user)
        flash("An email has been send to your email-address", 'success')
        return redirect(url_for('login'))
    return render_template('reset_request.html', parameter=parameters,
                           form=form, title='Reset Password', show_navbar=False)


def send_reset_mail(user):
    token = user.get_reset_token()
    mail.send_message('Password Reset Request Token has been raised', # heading of the mail
                      sender='noreplay@reset.com',  # sender name is the commenters email
                      recipients=[user.email],
                      body=f"""To reset your password click on the link
{url_for('reset_password', token=token, _external=True)}\n\n\n
If you didn't raise the reset request please ignore this email and no changes will be counted.\n\n
This token will be valid for 5 min.\n\n
                               ---- Thank you ----
"""# main body
                      )


@app.route('/reset_password/<token>', methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if not user:
        flash("Sorry, the token generated has been expired!!!", 'warning')
        return redirect(reset_request)
    form = PasswordResetForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  # password encryption
        user.password = hashed_password
        db.session.commit()
        flash(f'The password has been successfully reset.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html', parameter=parameters,
                           form=form, title='Reset Password', show_navbar=False)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/about')
def about():
    return render_template('about.html', title='About Us', user=current_user, parameter=parameters, show_navbar=True)


@app.route('/post/<string:slug>', methods=['GET'])  # build the custom redirecting url with slug
def posts(slug):
    post = Post.query.filter_by(
        slug=slug).first_or_404()  # query to find the entered slug's post or return 404 page error
    return render_template('posts.html', title='Post', user=current_user, parameter=parameters, post=post,
                           show_navbar=True)


@app.route('/post/<string:slug>/update', methods=['GET', "POST"])  # Update a post
@login_required
def post_update(slug):
    post = Post.query.filter_by(
        slug=slug).first_or_404()  # query to find the entered slug's post or return 404 page error
    if current_user.name != post.publisher:
        flash('You can\'t update the post', 'danger')  # you can use abort(403) directly also
        return redirect(url_for('home'))
    form = Postsubmitform()
    slug = ''
    image = url_for('static', filename='img/profile_pics/' + current_user.image_file)  # showing the image in account
    if form.validate_on_submit():
        for word in form.tagline.data.split():
            slug += (word + '-')  # building the slug from tag line
        slug = slug[:-1]  # deletion of the last '-'
        post.heading = form.title.data
        post.tag_line = form.tagline.data
        post.slug = slug
        post.content = form.content.data
        db.session.commit()
        flash("Your post has been updated.", 'success')
        return redirect(url_for('home'))
    elif request.method == 'GET':
        form.title.data = post.heading  # showing the current name
        form.tagline.data = post.tag_line  # showing the current email address
        form.content.data = post.content
    return render_template('update_post.html', title='Update Post', parameter=parameters, form=form, post=post,
                           image=image, show_navbar=False)


@app.route('/post/<string:slug>/delete', methods=["POST"])  # Update a post
@login_required
def deletepost(slug):
    post = Post.query.filter_by(
        slug=slug).first_or_404()  # query to find the entered slug's post or return 404 page error
    if current_user.name != post.publisher:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Your post has been deleted.", 'success')
    return redirect(url_for('home'))


@app.route('/user/<string:name>', methods=['GET'])  # build the custom redirecting url with slug
def all_posts(name):
    page = request.args.get('page', 1, type=int)
    # find if that user exists
    user = User.query.filter_by(name=name).first_or_404()
    post = Post.query.filter_by(author=user) \
        .order_by(desc(Post.date)) \
        .paginate(page=page, per_page=parameters['no_of_post_in_Homepage'])
    return render_template('all_posts.html', title='User Details', user=user, parameter=parameters, posts=post,
                           show_navbar=False)


@app.route('/contact', methods=["GET", "POST"])
def contact():
    if request.method == "POST":  # if it's a POST request (ie. Submit button is pressed)
        # Then Fetch all the values
        date_ = datetime.today().strftime('%Y-%m-%d %H:%M:%S')  # capture the date of the current day
        name_ = request.form.get('name')
        comment_ = request.form.get('msg')
        email_ = request.form.get('email')  # method-2 of taking value from html field
        phone_no_ = request.form.get('phone')
        # Now make an Entry through the Comment Class with the fetched entry
        entry = Comment(name=name_, comment=comment_, email=email_, phone_no=phone_no_, date=date_)
        db.session.add(entry)  # make the entry  # mysqldb is not supported by python 3x -> install mysqlclient
        db.session.commit()  # save the entry
        # send email to me also
        mail.send_message('New comment submitted by ' + name_,  # heading of the mail
                          sender=email_,  # sender name is the commenters email
                          recipients=[parameters["Mail_User_Name"]],
                          body=comment_ + "\nPhone number : " + phone_no_  # main body
                          )

    return render_template('contact.html', title='Contact Us', user=current_user, parameter=parameters,
                           show_navbar=True)


@app.route('/new-post/', methods=["GET", "POST"])
@login_required
def post_entry():
    slug = ''
    form = Postsubmitform()
    if form.validate_on_submit():
        date = datetime.today().strftime('%Y-%m-%d %H:%M:%S')  # capture the date of the current day
        # building slug
        for word in form.tagline.data.split():
            slug += (word + '-')  # building the slug from tag line
        slug = slug[:-1]  # deletion of the last '-'
        post = Post(heading=form.title.data, tag_line=form.tagline.data, slug=slug, content=form.content.data,
                    publisher=current_user.name, author=current_user, date=date)
        # saving
        db.session.add(post)
        db.session.commit()
        # send email to me also
        mail.send_message('New blog post written by ' + current_user.name,  # heading of the mail
                          sender=current_user.email,  # sender name is the poster's email
                          recipients=[parameters["Mail_User_Name"]],
                          body=f"Heading :{form.title.data} \nTag Line : {form.tagline.data}"
                               f" \nContent : {form.content.data} \nslug : {slug}"
                          # main body
                          )
        flash('Post has been added to the list', 'success')
        return redirect(url_for('home'))
    return render_template('new_posts.html', form=form, title='Submit Post', user=current_user, parameter=parameters,
                           show_navbar=True)
