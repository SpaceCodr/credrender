import os
import subprocess
import sys
import datetime
import logging
import ffmpeg_streaming
from ffmpeg_streaming import Formats, Bitrate, Representation, Size



from flask import (
    Flask,
    render_template,
    redirect,
    flash,
    url_for,
    session,
    request,
    Response
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from run import create_app,db,login_manager,bcrypt
from models import User,Videos
from forms import login_form,register_form


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User,int(user_id))
    # return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=1)

# Define the route for adding video metadata
@app.route('/addmetavideo/', methods=['GET', 'POST'],strict_slashes=False)
def add_video():
    if request.method == 'POST':
        # Get the video metadata from the form
        title = request.form['title']
        ownership = request.form['ownership']
        genre = request.form['genre']
        release_year = request.form['release_year']
        bio = request.form['bio']
        media_type = request.form['media_type']

        # Create a new Videos object with the metadata
        video = Videos(title=title, ownership=ownership, genre=genre,
                       release_year=release_year, bio=bio,
                       media_type=media_type)

        # Add the video to the database
        db.session.add(video)
        db.session.commit()

        # Redirect to the home page
        return redirect(url_for('sussubmit'))

    # If the request method is GET, render the form
    return render_template('add_video.html')

# Define the route for displaying the content of the Videos table
@app.route('/showvideosdb')
def show_videos():
    # Get all the videos from the database
    videos = Videos.query.all()

    # Render the template and pass in the videos
    return render_template('videosdb.html', videos=videos)

@app.route('/delete_video/<int:id>', methods=['GET', 'POST'])
def delete_video(id):
    video = Videos.query.get_or_404(id)
    db.session.delete(video)
    db.session.commit()
    return redirect(url_for('show_videos'))

@app.route("/sussubmit/",strict_slashes=False)
def sussubmit():
    return 'Submitted'

@app.route("/", methods=("GET", "POST"), strict_slashes=False)
def index():
    return render_template("index2.html",title="Home")


@app.route("/login/", methods=("GET", "POST"), strict_slashes=False)
def login():
    form = login_form()

    if form.validate_on_submit():
        try:
            user = User.query.filter_by(email=form.email.data).first()
            if check_password_hash(user.pwd, form.pwd.data):
                login_user(user)
                return redirect(url_for('index'))
            else:
                flash("Invalid Username or password!", "danger")
        except Exception as e:
            flash(e, "danger")

    return render_template("auth.html",
        form=form,
        text="Login",
        title="Login",
        btn_action="Login"
        )



# Register route
@app.route("/register/", methods=("GET", "POST"), strict_slashes=False)
def register():
    form = register_form()
    if form.validate_on_submit():
        try:
            email = form.email.data
            pwd = form.pwd.data
            username = form.username.data
            
            newuser = User(
                username=username,
                email=email,
                pwd=bcrypt.generate_password_hash(pwd),
            )
    
            db.session.add(newuser)
            db.session.commit()
            flash(f"Account Succesfully created", "success")
            return redirect(url_for("login"))

        except InvalidRequestError:
            db.session.rollback()
            flash(f"Something went wrong!", "danger")
        except IntegrityError:
            db.session.rollback()
            flash(f"User already exists!.", "warning")
        except DataError:
            db.session.rollback()
            flash(f"Invalid Entry", "warning")
        except InterfaceError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except DatabaseError:
            db.session.rollback()
            flash(f"Error connecting to the database", "danger")
        except BuildError:
            db.session.rollback()
            flash(f"An error occured !", "danger")
    return render_template("auth.html",
        form=form,
        text="Create account",
        title="Register",
        btn_action="Register account"
        )

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/viewlist")
@login_required
def viewlist():
    videos=Videos.query.all()
    return render_template("content.html",videos=videos,title="Videos")

@app.route('/video/<int:video_id>')
@login_required
def video(video_id):
    video=Videos.query.get_or_404(video_id)
    videofile=ffmpeg_streaming.input('static/videos/'+video.title)
    
    logging.basicConfig(filename='streaming.log', level=logging.NOTSET, format='[%(asctime)s] %(levelname)s: %(message)s')


    def monitor(ffmpeg, duration, time_, time_left, process):
        per = round(time_ / duration * 100)
        sys.stdout.write(
            "\rTranscoding...(%s%%) %s left [%s%s]" %
            (per, datetime.timedelta(seconds=int(time_left)), '#' * per, '-' * (100 - per))
        )
        sys.stdout.flush()


    # _360p  = Representation(Size(640, 360), Bitrate(276 * 1024, 128 * 1024))
    _480p  = Representation(Size(854, 480), Bitrate(750 * 1024, 192 * 1024))
    _720p  = Representation(Size(1280, 720), Bitrate(2048 * 1024, 320 * 1024))
    dash = videofile.dash(Formats.h264())
    dash.representations(_720p)

    if videofile.hls_output:
        dash.generate_hls_playlist()

    # dash.output('http://127.0.0.1:4000/videosfiles/dash.mpd', monitor=monitor)
    dash.output(monitor=monitor)
    # hls = videofile.hls(Formats.h264())
    # hls.auto_generate_representations()
     







    # # print(video.title)
    # videofile=ffmpeg_streaming.input('static/videos/'+video.title)

    # _144p  = Representation(Size(256, 144), Bitrate(95 * 1024, 64 * 1024))
    # _240p  = Representation(Size(426, 240), Bitrate(150 * 1024, 94 * 1024))
    # _360p  = Representation(Size(640, 360), Bitrate(276 * 1024, 128 * 1024))
    # _480p  = Representation(Size(854, 480), Bitrate(750 * 1024, 192 * 1024))
    # _720p  = Representation(Size(1280, 720), Bitrate(2048 * 1024, 320 * 1024))
    # _1080p = Representation(Size(1920, 1080), Bitrate(4096 * 1024, 320 * 1024))
    # _2k    = Representation(Size(2560, 1440), Bitrate(6144 * 1024, 320 * 1024))
    # _4k    = Representation(Size(3840, 2160), Bitrate(17408 * 1024, 320 * 1024))
    # dash = videofile.dash(Formats.h264())
    # hls.representations(_144p, _240p, _360p, _480p, _720p, _1080p, _2k, _4k)
    # dash.representations(_144p, _240p, _360p, _480p, _720p, _1080p, _2k, _4k)
    # dash.output(monitor=monitor)
    # hls.output(monitor=monitor) 

    # video = ffmpeg_streaming.input('static/videos/ice2.m3u8')

    # stream = video.stream2file(Formats.h264())
    # stream.output()

    return render_template('video.html',videofile=videofile)

    # # Specify the path to your video file
    # video_path = '/static/videos/'+video.title

    # # Open a subprocess to ffmpeg and read the video frame by frame
    # cmd = ['ffmpeg', '-i', video_path, '-f', 'image2pipe', '-pix_fmt', 'rgb24', '-vcodec', 'rawvideo', '-']
    # proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    # # Yield the video frame by frame
    # while True:
    #     frame = proc.stdout.read(1024*1024)
    #     if not frame:
    #         break
    #     yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    # # Close the subprocess
    # proc.kill()
    # return Response(content_type='multipart/x-mixed-replace; boundary=frame')






# @app.route('/video/<int:video_id>')
# @login_required
# def video(video_id):
#     video = Videos.query.get_or_404(video_id)
#     # Check if video exists in the specified path
#     if not os.path.isfile('static/videos/'+video.title):
#         return 'Video not found', 404

#     range_header = request.headers.get('Range', None)
#     video_size = os.path.getsize('static/videos/'+video.title)

#     if range_header:
#         start, end = range_header.split('=')[1].split('-')
#         start = int(start)
#         end = int(end) if end else video_size - 1
#     else:
#         start = 0
#         end = video_size - 1

#     length = end - start + 1

#     headers = {
#         'Content-Type': 'video/mp4',
#         'Content-Length': length,
#         'Content-Range': f"bytes {start}-{end}/{video_size}",
#         'Accept-Ranges': 'bytes',
#     }

#     p = subprocess.Popen(['ffmpeg', '-i', 'static/videos/'+video.title , '-ss', str(start), '-vframes', str(length), '-f', 'mp4', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#     return Response(
#         p.stdout,
#         status=206 if range_header else 200,
#         headers=headers,
#         direct_passthrough=True,
#     )

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=4000)