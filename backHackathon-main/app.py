import cv2
import os

from flask import Flask, request, jsonify
from flask_cors import CORS

import easyocr
from deepface import DeepFace


app = Flask(__name__)

CORS(app)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/process_document', methods=['POST'])
def process_document():
    global file_path_udostak, file_path_prava
    document_image_udostak = request.files['documentImage1']
    document_image_prava = request.files['documentImage2']
    
    file_path_udostak = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image1.png')
    file_path_prava = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image2.png')
    
    document_image_udostak.save(file_path_udostak)
    document_image_prava.save(file_path_prava)
    
    result = DeepFace.verify(file_path_udostak, file_path_prava)
    if result['verified']:
        if checkApprove():
            result = check_iin(*ai_moment())
        else:
            result = "False"
    else:
        result = "False. Faces not matched"
    
    return jsonify({'result': result})

def textRecognition(file_path):
    reader = easyocr.Reader(["ru"], gpu = True , verbose = False)
    image = cv2.imread(file_path)
    result = reader.readtext(image, detail= 0)
    return result

def textRecognitionEnglish(file_path):
    reader = easyocr.Reader(["en"], gpu = True , verbose = False)
    image = cv2.imread(file_path)
    result = reader.readtext(image, detail= 0)
    return result

def udastakBirthdayRecognition():
    for info in textRecognition(file_path_udostak):
        if "." in info:
            return info

def pravaBirthdayRecognition():
    for info in textRecognitionEnglish(file_path_prava):
        if "3." in info:
            info = info[3:13]
            return info

def udastakIinRecognition():
    for info in textRecognitionEnglish(file_path_udostak):
        if info.isdigit() and len(info) == 12:
            return info

def pravaIinRecognition():
    iins = []
    for info in textRecognitionEnglish(file_path_prava):
        if "XCHLIN" in info:
            iin = "".join(char for char in info if char.isdigit())
            iin = iin[1:]
            iins.append(iin)
            
    return ",".join(iins)


def compareIIN():
    if udastakIinRecognition() == pravaIinRecognition():
        return True
    else:
        return False

def compareBirthday():
    if udastakBirthdayRecognition() == pravaBirthdayRecognition():
        return True
    else:
        return False

def checkApprove():
    if compareBirthday() and compareIIN():
        return True
    else:
        return False

def birthdayRecognition():
    for info in textRecognition(file_path_udostak):
        if "." in info:
            return info
        
def iinRecognition():
    for info in textRecognition(file_path_udostak):
        if info.isdigit() and len(info) == 12:
            return info

def ai_moment():
    return (iinRecognition(), birthdayRecognition())

def check_iin(iin, birthday):
    if len(iin) != 12 or not iin.isnumeric():
        return "Invalid IIN"
    year_iin = int(iin[0:2])
    month_iin = int(iin[2:4])
    day_iin = int(iin[4:6])
    year_birthday = int(birthday[8:])
    month_birthday = int(birthday[3:5])
    day_birthday = int(birthday[0:2])
    if year_iin != year_birthday or month_iin != month_birthday or day_iin != day_birthday:
        return "Invalid id card"
    if int(iin[11]) == check12digit(iin):
        return "IIN is correct"
    else:
        return "Invalid"

def check12digit(iin):
    weights1 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    weights2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2]

    sum1 = sum(int(digit) * weight for digit, weight in zip(iin, weights1))
    control_digit1 = sum1 % 11

    if control_digit1 == 10:
        sum2 = sum(int(digit) * weight for digit, weight in zip(iin, weights2))
        control_digit2 = sum2 % 11
        if control_digit2 == 10:
            return None
        else:
            return control_digit2
    else:
        return control_digit1


if __name__ == '__main__':
    app.run(debug=True, port=5000)
    