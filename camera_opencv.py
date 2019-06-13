from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, Response
import cv2
import face_recognition
import datetime
from IntellFRS.base_camera import BaseCamera
import os
import psycopg2
import glob
from pathlib import Path
from IntellFRS.models import User, Attendance
from IntellFRS import db

face_name=[]
name="Unknown"
id_name= 0
name2=""
filename=""

class Camera(BaseCamera):
    video_source = 0
    username=[]

    @staticmethod
    def set_video_source(source):
        Camera.video_source = source

    @staticmethod
    def frames():
        global face_names
        global name
        global id_name
        global filename
        global name2
        c = datetime.datetime.now()
        files = []

        #files = glob.glob("/home/mukund/IntellFRS/static/temp_img/*.jpg")
        #res=ModelName.query.filter(ModelName.var1==cond).order_by(ModelName.var1.desc())
        #files1 = db.session.query(User.image_file).all()
        files1 = db.session.query(User.image_file).order_by(User.id).all()
        for f1 in files1:
            files.append(f1[0])
        i_names=[]
        user_image = []
        user_face_encoding = []
        known_face_encodings = []
        known_face_names = []

        for f in files:
            i_names.append(Path(f).name)
            user_image.append(face_recognition.load_image_file(f))
        for ui in user_image:
            user_face_encoding.append(face_recognition.face_encodings(ui)[0])

        for ufe in user_face_encoding:
            known_face_encodings.append(ufe)

        for i in i_names:
            t=os.path.splitext(i)[0]
            #print("rrrrrrrtyyy",t)
            f=db.session.query(User.name).filter_by(id=t).first()
            known_face_names.append(f[0])
            #id_name = t
            #known_ids.append(t)
            #print(f)

        face_locations = []
        face_encodings = []
        face_names = []
        process_this_frame = True

        #print("known face names",known_face_names)

        camera = cv2.VideoCapture(Camera.video_source)

        if not camera.isOpened():
            raise RuntimeError('Could not start camera.')

        while True:
            # read current frame
            _, frame = camera.read()

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            if process_this_frame:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings= face_recognition.face_encodings(rgb_small_frame, face_locations)
                face_names = []
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
                    name = "Unknown"
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = known_face_names[first_match_index]
                        first_match_index = first_match_index+1
                        #id_name = db.session.query(User.id).filter_by(id=first_match_index).first()
                        id_name = first_match_index
                        name2=name
                    else:
                        r = db.session.query(db.func.count(User.id)).scalar()
                        r+=1
                        n = str(r)+'.jpg'
                        orig=cv2.imencode('.jpg', frame)[1]
                        os.chdir('/home/disha/IntellFRS/static/profile_pics')
                        filename = os.path.abspath(n)
                        print("filename",filename)
                        name2 = name
                        with open(filename,'wb') as f:
                            f.write(orig)
                    face_names.append(name)

            process_this_frame = not process_this_frame

            for (top, right, bottom, left), name in zip(face_locations, face_names):
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                n = "("+ name+ ") " + c.strftime("%I:%M:%S %p")
                cv2.putText(frame, n, (left + 10, bottom - 6), font, fontScale=0.75, color=(255, 255, 255), thickness=1)

            yield cv2.imencode('.jpg', frame)[1].tobytes()

    @staticmethod
    def ret_names():
        global name2
        global id_name
        return id_name,name2

    @staticmethod
    def ret_path():
        global filename
        return filename
