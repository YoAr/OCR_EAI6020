import cv2
import pytesseract
import os

def ocr(file_path):
    image = cv2.imread(file_path)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image,config=custom_config)
    print(text)

def readAll():
    path = "/Users/yoar/Workspace/image source"
    os.chdir(path)
    for file in os.listdir():
        if file.endswith(".jpg"):
            file_path = f"{path}/{file}"

            #print(file_path)
            ocr(file_path)

readAll()

#Business questions
#Death based on age
#Male / Female
#Cluster on Street address
#Veteren
