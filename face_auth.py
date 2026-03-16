import face_recognition
import cv2

def authenticate_user():

    my_image = face_recognition.load_image_file("my_face.jpg")
    my_face_encoding = face_recognition.face_encodings(my_image)[0]

    known_face_encodings = [my_face_encoding]

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        rgb_frame = frame[:, :, ::-1]

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:

            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            if True in matches:
                print("Trevor detected!")

                cap.release()
                cv2.destroyAllWindows()

                return True

        cv2.imshow("Face Login", frame)

        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

    return False