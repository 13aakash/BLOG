from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import os

app = Flask(__name__)

# --- CONFIGURATION ---
# Absolute path to ensure DB works on Render/Web
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'blog.database')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'super_secret_key'  # Needed for Admin Session
db = SQLAlchemy(app)

# --- MODEL ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    body = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(20), default=datetime.now().strftime("%Y-%m-%d"))

    def to_dict(self):
        return {"id": self.id, "title": self.title, "body": self.body, "date": self.date}

# Create DB if not exists
with app.app_context():
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))
    db.create_all()

# --- API ENDPOINT (For Resume Claim) ---
@app.route('/api/posts')
def get_posts_api():
    posts = Post.query.order_by(Post.id.desc()).all()
    return jsonify([post.to_dict() for post in posts])

# --- PUBLIC ROUTES ---
@app.route('/')
def home():
    search_query = request.args.get('q')
    sort_order = request.args.get('sort', 'newest')
    
    query = Post.query
    
    # Search Logic
    if search_query:
        query = query.filter((Post.title.contains(search_query)) | (Post.body.contains(search_query)))
    
    # Sort Logic
    if sort_order == 'oldest':
        posts = query.order_by(Post.id.asc()).all()
    else:
        posts = query.order_by(Post.id.desc()).all()

    return render_template('index.html', posts=[p.to_dict() for p in posts], sort_order=sort_order)

@app.route('/post/<int:post_id>')
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post.to_dict())

# --- ADMIN ROUTES (Protected) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Hardcoded Admin Credentials
        if request.form['username'] == 'admin' and request.form['password'] == 'admin123':
            session['user'] = 'admin'
            return redirect(url_for('home'))
        else:
            return "Invalid Username or Password. <a href='/login'>Try Again</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if not session.get('user'): return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_post = Post(title=request.form['title'], body=request.form['body'])
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    if not session.get('user'): return redirect(url_for('login'))
    post = Post.query.get_or_404(id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.body = request.form['body']
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('edit.html', post=post)

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('user'): return redirect(url_for('login'))
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)