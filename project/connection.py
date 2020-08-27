from project import db, login_manager, parameters,app
from datetime import datetime
# login_manager expect User has certain 4 attributes in necessary like is_authenticated, is_anonymous, is_active and
# one method named get_id but as this is common UserMixin class provide us with all of this. All we need is to inherit
# User class from this class
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer  # generate token for 30 sec for verification


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Comment(db.Model):
    s_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(40), nullable=False)
    phone_no = db.Column(db.String(13), nullable=False)
    date = db.Column(db.String(20), nullable=True)


class Post(db.Model):
    s_no = db.Column(db.Integer, primary_key=True)
    heading = db.Column(db.String(120), unique=True, nullable=False)
    tag_line = db.Column(db.String(150), unique=True, nullable=False)
    slug = db.Column(db.String(40), unique=True, nullable=False)
    content = db.Column(db.Text, unique=True, nullable=False)
    publisher = db.Column(db.String(20), db.ForeignKey('user.name'), nullable=False)
    date = db.Column(db.String(20), nullable=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), unique=True, nullable=False)
    image_file = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    # 'author' is a back reference for 'User' to access 'Post' table.
    # 'posts' doesn't exist in original table. It basically add an internal query for the access

    def get_reset_token(self, expire_period=parameters['User_validation_expire_time_period']):
        s = Serializer(app.config['SECRET_KEY'], expire_period)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)
