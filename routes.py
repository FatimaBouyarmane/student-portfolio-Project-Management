import os
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request, abort, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
try:
    # For newer versions of Werkzeug
    from werkzeug.urls import url_parse
except ImportError:
    # For older versions of Werkzeug
    from urllib.parse import urlparse as url_parse

# Try to import Github, but continue if it fails
try:
    from github import Github
    GITHUB_ENABLED = True
except ImportError:
    GITHUB_ENABLED = False
    print("GitHub integration is disabled. Install PyGithub to enable this feature.")

from app import app, db, mail, ts
from models import User, Project, Comment, Notification, UserStyle
from forms import (RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm,
                  UpdateProfileForm, CommentForm, StyleForm, ProjectForm)


@app.route('/')
def index():
    """Home page route."""
    return render_template('index.html', title='Welcome to Student Portfolio')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        
        # Check if email is enabled
        from app import MAIL_ENABLED
        
        if MAIL_ENABLED:
            # Generate confirmation token
            token = ts.dumps(user.email, salt='email-confirm-key')
            
            # Send confirmation email
            confirm_url = url_for('confirm_email', token=token, _external=True)
            subject = "Please confirm your email"
            html = render_template('emails/confirmation.html', confirm_url=confirm_url)
            
            try:
                msg = Message(subject=subject, recipients=[user.email], html=html)
                mail.send(msg)
                flash('A confirmation email has been sent to your email address. Please check your inbox.', 'info')
            except Exception as e:
                app.logger.error(f"Email sending error: {str(e)}")
                # If email fails, still register but set confirmed to True
                user.confirmed = True
                user.confirmed_on = datetime.utcnow()
                flash('Account created successfully! Email confirmation is currently unavailable.', 'success')
        else:
            # If email is not configured, automatically confirm the user
            user.confirmed = True
            user.confirmed_on = datetime.utcnow()
            flash('Account created successfully!', 'success')
        
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)


@app.route('/confirm/<token>')
def confirm_email(token):
    """Email confirmation route."""
    try:
        email = ts.loads(token, salt='email-confirm-key', max_age=86400)  # 24 hours expiration
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(email=email).first()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.utcnow()
        db.session.commit()
        flash('Thank you for confirming your email!', 'success')
    
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('login'))
        
        # Check if email is enabled before enforcing confirmation
        from app import MAIL_ENABLED
        
        if MAIL_ENABLED and not user.confirmed:
            flash('Please confirm your email address before logging in.', 'warning')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('portfolio')
        
        return redirect(next_page)
    
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    """User logout route."""
    logout_user()
    return redirect(url_for('index'))


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    """Password reset request route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Check if email is enabled
    from app import MAIL_ENABLED
    
    if not MAIL_ENABLED:
        flash('Password reset via email is currently unavailable. Please contact support.', 'warning')
        return redirect(url_for('login'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate reset token
            token = ts.dumps(user.email, salt='password-reset-key')
            
            # Send reset email
            reset_url = url_for('reset_token', token=token, _external=True)
            subject = "Password Reset Request"
            html = render_template('emails/reset_password.html', reset_url=reset_url)
            
            try:
                msg = Message(subject=subject, recipients=[user.email], html=html)
                mail.send(msg)
                flash('An email has been sent with instructions to reset your password.', 'info')
            except Exception as e:
                app.logger.error(f"Email sending error: {str(e)}")
                flash('Error sending password reset email. Please try again later.', 'danger')
        else:
            # Don't reveal if a user exists or not for security
            flash('An email has been sent with instructions to reset your password (if the account exists).', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    """Password reset with token route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    try:
        email = ts.loads(token, salt='password-reset-key', max_age=3600)  # 1 hour expiration
    except:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('reset_request'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', title='Reset Password', form=form)


@app.route('/portfolio')
@login_required
def portfolio():
    """User portfolio route."""
    projects = Project.query.filter_by(user_id=current_user.id).all()
    return render_template('portfolio.html', title='My Portfolio', projects=projects)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile route."""
    form = UpdateProfileForm(
        original_username=current_user.username,
        original_email=current_user.email
    )
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data
        current_user.github_username = form.github_username.data
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
        form.github_username.data = current_user.github_username
    
    return render_template('profile.html', title='Profile', form=form)


@app.route('/import_projects', methods=['GET', 'POST'])
@login_required
def import_projects():
    """GitHub project import route."""
    # Check if GitHub integration is enabled
    if not GITHUB_ENABLED:
        flash('GitHub integration is currently disabled. Please try again later.', 'warning')
        return redirect(url_for('portfolio'))
        
    if request.method == 'POST':
        github_username = request.form.get('github_username')
        
        if not github_username:
            flash('Please enter your GitHub username.', 'danger')
            return redirect(url_for('import_projects'))
        
        try:
            # Initialize GitHub API
            github_token = os.environ.get('GITHUB_TOKEN')
            g = Github(github_token) if github_token else Github()
            
            # Get the user's public repositories
            user = g.get_user(github_username)
            github_repos = user.get_repos()
            
            # Check if repos are being selected for import or just displaying repos
            selected_repos = request.form.getlist('repos')
            
            if selected_repos:
                # User has selected repos to import
                imported_count = 0
                
                for repo_name in selected_repos:
                    repo = g.get_repo(f"{github_username}/{repo_name}")
                    
                    # Check if project already exists
                    existing_project = Project.query.filter_by(
                        user_id=current_user.id,
                        github_id=str(repo.id)
                    ).first()
                    
                    if not existing_project:
                        # Create new project
                        project = Project(
                            title=repo.name,
                            description=repo.description or "",
                            repo_url=repo.html_url,
                            github_id=str(repo.id),
                            technologies=", ".join(list(repo.get_languages().keys())),
                            user_id=current_user.id
                        )
                        db.session.add(project)
                        imported_count += 1
                
                if imported_count > 0:
                    db.session.commit()
                    flash(f'Successfully imported {imported_count} projects from GitHub!', 'success')
                else:
                    flash('No new projects were imported.', 'info')
                
                return redirect(url_for('portfolio'))
            else:
                # User is just fetching repos to display
                repos = []
                for repo in github_repos:
                    # Format repos for display
                    repos.append({
                        'name': repo.name,
                        'description': repo.description,
                        'fork_count': repo.forks_count,
                        'star_count': repo.stargazers_count,
                        'updated_at': repo.updated_at.strftime('%Y-%m-%d')
                    })
                return render_template('import_projects.html', title='Import GitHub Projects', repos=repos, github_username=github_username)
        
        except Exception as e:
            app.logger.error(f"GitHub import error: {str(e)}")
            flash(f'Error importing GitHub projects: {str(e)}', 'danger')
            return redirect(url_for('import_projects'))
    
    return render_template('import_projects.html', title='Import GitHub Projects')


@app.route('/projects/<int:project_id>')
def project_detail(project_id):
    """Project detail route."""
    project = Project.query.get_or_404(project_id)
    comments = Comment.query.filter_by(project_id=project.id).order_by(Comment.created_at.desc()).all()
    form = CommentForm()
    return render_template('project_detail.html', title=project.title, project=project, comments=comments, form=form)


@app.route('/projects/new', methods=['GET', 'POST'])
@login_required
def create_project():
    """Create a new project."""
    form = ProjectForm()
    
    if form.validate_on_submit():
        project = Project(
            title=form.title.data,
            description=form.description.data,
            technologies=form.technologies.data,
            repo_url=form.repo_url.data,
            live_url=form.live_url.data,
            project_color=form.project_color.data,
            user_id=current_user.id
        )
        
        # Handle project image upload if provided
        if form.project_image.data:
            # Ensure uploads directory exists
            upload_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate a secure filename
            from werkzeug.utils import secure_filename
            import time
            filename = secure_filename(form.project_image.data.filename)
            unique_filename = f"project_{int(time.time())}_{filename}"
            
            # Save the file
            filepath = os.path.join('uploads', unique_filename)
            form.project_image.data.save(os.path.join(app.static_folder, filepath))
            
            # Update project with image path
            project.image_url = os.path.join('/static', filepath)
        
        db.session.add(project)
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('portfolio'))
    
    return render_template('edit_project.html', title='Create Project', form=form, is_new=True)


@app.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Edit an existing project."""
    project = Project.query.get_or_404(project_id)
    
    # Check if user owns the project
    if project.user_id != current_user.id:
        flash('You do not have permission to edit this project.', 'danger')
        return redirect(url_for('portfolio'))
    
    form = ProjectForm()
    
    if form.validate_on_submit():
        project.title = form.title.data
        project.description = form.description.data
        project.technologies = form.technologies.data
        project.repo_url = form.repo_url.data
        project.live_url = form.live_url.data
        project.project_color = form.project_color.data
        
        # Handle project image upload if provided
        if form.project_image.data:
            # Ensure uploads directory exists
            upload_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate a secure filename
            from werkzeug.utils import secure_filename
            import time
            filename = secure_filename(form.project_image.data.filename)
            unique_filename = f"project_{int(time.time())}_{filename}"
            
            # Save the file
            filepath = os.path.join('uploads', unique_filename)
            form.project_image.data.save(os.path.join(app.static_folder, filepath))
            
            # Update project with image path
            project.image_url = os.path.join('/static', filepath)
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    elif request.method == 'GET':
        form.title.data = project.title
        form.description.data = project.description
        form.technologies.data = project.technologies
        form.repo_url.data = project.repo_url
        form.live_url.data = project.live_url
        form.project_color.data = project.project_color
    
    return render_template('edit_project.html', title='Edit Project', form=form, project=project, is_new=False)


@app.route('/projects/<int:project_id>/comment', methods=['POST'])
@login_required
def add_comment(project_id):
    """Add comment to project route."""
    project = Project.query.get_or_404(project_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            project_id=project.id,
            author_id=current_user.id
        )
        db.session.add(comment)
        db.session.commit()
        
        # Create notification for project owner
        if project.user_id != current_user.id:
            notification = Notification(
                message=f"{current_user.username} commented on your project '{project.title}'",
                user_id=project.user_id,
                comment_id=comment.id
            )
            db.session.add(notification)
            db.session.commit()
        
        flash('Your comment has been posted!', 'success')
    else:
        flash('There was an error posting your comment.', 'danger')
    
    return redirect(url_for('project_detail', project_id=project.id))


@app.route('/notifications')
@login_required
def notifications():
    """User notifications route."""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    
    # Mark all as read
    for notification in notifications:
        if not notification.read:
            notification.read = True
    
    db.session.commit()
    
    return render_template('notifications.html', title='Notifications', notifications=notifications)


@app.route('/check_notifications')
@login_required
def check_notifications():
    """API route to check for unread notifications."""
    unread_count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify({'unread_count': unread_count})


@app.route('/download_source')
def download_source():
    """Download the source code as a zip file."""
    import zipfile
    import tempfile
    import os
    from io import BytesIO
    from flask import send_file
    
    memory_file = BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Get base path
        base_path = os.path.abspath(".")
        
        # Add Python files
        for root, dirs, files in os.walk(base_path):
            # Skip hidden directories and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__' and d != '.git']
            
            for file in files:
                # Skip hidden files and .pyc files
                if file.startswith('.') or file.endswith('.pyc') or file == '.env':
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_path)
                zipf.write(file_path, arcname)
    
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name='student-portfolio-source.zip'
    )


@app.context_processor
def utility_processor():
    """Context processor to add utility functions to templates."""
    def unread_notifications_count():
        if current_user.is_authenticated:
            return Notification.query.filter_by(user_id=current_user.id, read=False).count()
        return 0
    
    return dict(unread_notifications_count=unread_notifications_count)


@app.route('/customize_style', methods=['GET', 'POST'])
@login_required
def customize_style():
    """Customize portfolio style route."""
    # Check if user already has a style, otherwise create one
    if not current_user.style:
        style = UserStyle(user_id=current_user.id)
        db.session.add(style)
        db.session.commit()
    
    form = StyleForm()
    
    if form.validate_on_submit():
        # Update style settings
        current_user.style.primary_color = form.primary_color.data
        current_user.style.secondary_color = form.secondary_color.data
        current_user.style.background_color = form.background_color.data
        current_user.style.font_family = form.font_family.data
        
        # Handle background image upload if provided
        if form.background_image.data:
            # Ensure uploads directory exists
            upload_dir = os.path.join(app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generate a secure filename
            from werkzeug.utils import secure_filename
            import time
            filename = secure_filename(form.background_image.data.filename)
            unique_filename = f"{int(time.time())}_{filename}"
            
            # Save the file
            filepath = os.path.join('uploads', unique_filename)
            form.background_image.data.save(os.path.join(app.static_folder, filepath))
            
            # Update database with relative path for static serving
            current_user.style.background_image = os.path.join('static', filepath)
        
        db.session.commit()
        flash('Your portfolio style has been updated!', 'success')
        return redirect(url_for('portfolio'))
    
    elif request.method == 'GET':
        # Pre-populate form with current values
        form.primary_color.data = current_user.style.primary_color
        form.secondary_color.data = current_user.style.secondary_color
        form.background_color.data = current_user.style.background_color
        form.font_family.data = current_user.style.font_family
    
    return render_template('customize_style.html', title='Customize Style', form=form)


@app.route('/export_pdf')
@login_required
def export_pdf():
    """Export portfolio to PDF."""
    try:
        import pdfkit
        from flask import make_response
        import os
        
        config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
        # Get user projects
        projects = Project.query.filter_by(user_id=current_user.id).all()
        
        # Generate HTML for the PDF
        html = render_template(
            'portfolio.html', 
            title=f"{current_user.username}'s Portfolio",
            projects=projects,
            export_mode=True
        )
        
        # Configure pdfkit
        options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8',
            'no-outline': None
        }
        
        # Create PDF from HTML
        pdf = pdfkit.from_string(html, False, options=options)
        
        # Create response
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={current_user.username}_portfolio.pdf'
        
        return response
    except ImportError:
        flash('PDF export is not available. Please install pdfkit to enable this feature.', 'warning')
        return redirect(url_for('portfolio'))
    except Exception as e:
        flash(f'Error exporting portfolio: {str(e)}', 'danger')
        return redirect(url_for('portfolio'))
