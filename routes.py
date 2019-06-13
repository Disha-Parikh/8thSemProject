from sqlalchemy.ext.declarative import DeclarativeMeta
from importlib import import_module
import os
import secrets
from PIL import Image
from flask import render_template, Response, url_for, flash, redirect, request, abort, jsonify
from IntellFRS import app, db, bcrypt
from IntellFRS.forms import RegistrationForm, LoginForm, UpdateAccountForm
from IntellFRS.models import User, Attendance
from flask_login import login_user, current_user, logout_user, login_required
from email.mime.text import MIMEText
import smtplib
import pycronofy
import datetime
import json


if os.environ.get('CAMERA'):
    Camera = import_module('camera_' + os.environ['CAMERA']).Camera
else:
    from IntellFRS.camera_opencv import Camera


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)


name = ""
id_name = 0
data = ()
imf = ""



@app.route('/')
def index():
    """particles"""
    return render_template('index.html')

def gen(camera):
    """Video streaming generator function."""
    #global name
    #_,name1 = Camera.ret_names()
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return render_template('vlogin.html')


@app.route('/fetchdata/', methods=['POST','GET'])
def fetchdata():
    global data
    global name
    global id_name
    id_name, name = Camera.ret_names()
    if(name =="Unknown"):
        return jsonify({'data':"Unknown"})
    else:
        data = User.query.filter_by(id = id_name).first()
        temp_dict = {'name':data.name, 'email': data.email, 'mobile': data.mobile, 'address': data.address}
        d = datetime.datetime.today()
        c_date = datetime.datetime.now()
        m = c_date.strftime("%-m")
        reg = db.session.query(User.id).filter_by(id = id_name).first()
        att = Attendance(name = name, pa = 'P', date = d, reg_no = reg[0])
        db.session.add(att)
        db.session.commit()
        return jsonify({'data':temp_dict})

def send_email(user, email):
    # from_e = os.environ.get('email')
    # from_p = os.environ.get('password')
    from_e= "intellfrs@gmail.com"
    from_p= "bcrypt@123"
    to_email=email
    subject="Registration"
    message="Hi <br> <strong>%r</strong>,  You have been registered successfully. <br> Thanks!" % (user)
    msg=MIMEText(message, 'html')
    msg['Subject']=subject
    msg['To']=to_email
    msg['From']=from_e
    gmail=smtplib.SMTP('smtp.gmail.com',587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_e, from_p)
    gmail.send_message(msg)



def send_events(user, email,eve):
    # from_e = os.environ.get('email')
    # from_p = os.environ.get('password')
    from_e= "intellfrs@gmail.com"
    from_p= "bcrypt@123"
    to_email=email
    subject="Registration"
    message="Your Events for the day are%r. <br> Thanks!" % (eve)
    msg=MIMEText(message, 'html')
    msg['Subject']=subject
    msg['To']=to_email
    msg['From']=from_e
    gmail=smtplib.SMTP('smtp.gmail.com',587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(from_e, from_p)
    gmail.send_message(msg)
    return


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
    	im = Camera.ret_path()
    	user = User(name=form.name.data, email=form.email.data, mobile=form.mobile.data, cal_id=form.cal_id.data, address = form.address.data, image_file=im)
    	db.session.add(user)
    	db.session.commit()
    	flash('Your account has been created! You are now able to log in', 'success')
    	send_email(form.name.data, form.email.data)
    	return redirect(url_for('logint'))
    return render_template('register.html', title='Register', form=form)


@app.route("/logint", methods=['GET', 'POST'])
def logint():
    # global name
    # global id_name
    id_name,name = Camera.ret_names()
    user = User.query.filter_by(id = id_name).first()
    form = LoginForm(obj=user)
    rform = RegistrationForm()
    if user:
        login_user(user, remember=form.remember.data)
        #next_page = request.args.get('next')
        #return redirect(next_page) if next_page else redirect(url_for('home'))
    #else:
    #    flash('Login Unsuccessful. Please Register', 'danger')
    #return render_template('register.html', title='Register', form=rform)
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    return render_template('show_events.html')


@app.route('/events')
@login_required
def events():
    # global id_name
    # global name
    global data
    id_name,name = Camera.ret_names()
    data = User.query.filter_by(id = id_name).first()
    cal_id = data.cal_id
    print(cal_id)
    cronofy = pycronofy.Client(access_token="hr3pyQW_wTYL1gF3QEWOb0w62lCl4SPk")
    timezone_id = 'Asia/Calcutta'
    from_date = datetime.date.today()
    to_date = (datetime.date.today() + datetime.timedelta(days=1))
    #YOUR_CAL_ID="cal_XG5nFdB2PnyyMAm3_6fMBWm5x3kiv34Wt5Zdb0Q"
    YOUR_CAL_ID = cal_id
    #send_email(data.name,data.email)
    all_events = cronofy.read_events(calendar_ids=(YOUR_CAL_ID,),
        from_date=from_date,
        to_date=to_date,
        tzid=timezone_id
    ).all()
    print(all_events)
    send_events(data.name,data.email,all_events)
    conv = json.dumps(all_events)
    return conv



@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/about")
def about():
    return render_template('about.html', title='About')


def save_picture(form_picture):
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = str(current_user.id) + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    #
    # output_size = (300, 300)
    # i = Image.open(form_picture)
    # i.thumbnail(output_size)
    # i.save(picture_path)
    form_picture.save(picture_path)
    return picture_fn, picture_path


@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file, picture_path = save_picture(form.picture.data)
            current_user.image_file = picture_path
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.name.data = current_user.name
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


'''data = [

        {Date:"1",present:"25"},{Date:"2",present:"26"}, {Date:"3",present:"27"}, {Date:"4",present:"28"},
        {Date:"5",present:"28"},{Date:"6",present:"28"}, {Date:"7",present:"26"}, {Date:"8",present:"31"},
        {Date:"9",present:"25"},{Date:"10",present:"21"},{Date:"11",present:"11"},{Date:"12",present:"31"}
];'''

#n = "("+ name+ ") " + c.strftime("%I:%M:%S %p")

@app.route("/attchart", methods=['GET', 'POST'])
@login_required
def attchart():
    global data
    id_name,name = Camera.ret_names()
    reg = db.session.query(User.id).filter_by(id = id_name).first()
    reg_n = reg[0]
    #months=["1","2","3","4","5","6","7","8","9","10","11","12"]
    months=[]
    for i in range(12):
        months.append(i+1)

    for i in range(12):
        dictt={"Date": months[i],"present":months[i]}
        dict1.append(dictt)
    for i in range(12):
        vard=months[i]
        dict1 =	{
        "Date": months[i],
        "present": present[i],
        }

    lista=[]
    for i in range(12):
        ac = Attendance.query.filter(Attendance.reg_no == id_name, Attendance.pa == 'P', Attendance.date== i).count()
        days.append(ac)

    for i in range(12):
        #lista.append("{Date:"+'"'+months[i]+'"'+",present:"+'"'+days[i]+'"'+"}")
        lista.append("{Date:"+months[i]+",present:"+days[i]+"}")
    print(lista)
    return lista
