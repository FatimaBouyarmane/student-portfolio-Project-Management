from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)
    profile_image = db.Column(db.String(256), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    github_username = db.Column(db.String(64), nullable=True)
    github_access_token = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='author', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True)
    style = db.relationship('UserStyle', backref='user', lazy=True, uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    repo_url = db.Column(db.String(256), nullable=True)
    live_url = db.Column(db.String(256), nullable=True)
    image_url = db.Column(db.String(256), nullable=True)
    github_id = db.Column(db.String(64), nullable=True)
    technologies = db.Column(db.String(256), nullable=True)
    project_color = db.Column(db.String(20), default="#0d6efd")  # Default Bootstrap primary blue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    comments = db.relationship('Comment', backref='project', lazy=True)
    
    def __repr__(self):
        return f'<Project {self.title}>'


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    author = db.relationship('User', backref='comments')
    
    def __repr__(self):
        return f'<Comment {self.id}>'


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Optional reference to a comment
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    comment = db.relationship('Comment', backref='notifications')
    
    def __repr__(self):
        return f'<Notification {self.id}>'


class UserStyle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    primary_color = db.Column(db.String(20), default="#0d6efd")  # Bootstrap primary blue
    secondary_color = db.Column(db.String(20), default="#6c757d")  # Bootstrap secondary gray
    background_color = db.Column(db.String(20), default="#212529")  # Bootstrap dark
    font_family = db.Column(db.String(100), default="'Roboto', sans-serif")
    background_image = db.Column(db.String(256), nullable=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<UserStyle {self.user_id}>'
