import cv2
import pytesseract
from pytesseract import Output
import os
import json
import numpy as np
import csv
import psycopg2
import matplotlib.pyplot as plt

finalJson = []

def convertToPng():
    path = os.getcwd()
    if('images' not in path):
        os.chdir(path)
    for file in os.listdir():
        if file.endswith(".jpg"):
            file_path = f"{path}/{file}"
            file_name = os.path.basename(file_path)
            file_name = file_name.replace(".jpg", "")
            png =cv2.imread(file_path, 1)
            cv2.imwrite(file_name+".png", png)

# get grayscale image
def get_grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# noise removal
def remove_noise(image):
    return cv2.medianBlur(image,5)
 
#thresholding
def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


#opening - erosion followed by dilation
def opening_image(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

#canny edge detection
def canny_image(image):
    return cv2.Canny(image, 100, 200)

def ocr(file_path):
    image = cv2.imread(file_path)
    #Optimization techniques | Did not work in this case
    # gray = get_grayscale(image)
    # thresh = thresholding(gray)
    # opening = opening_image(thresh)
    # canny = canny_image(gray)
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image,config=custom_config)
    # print(text)
    length = len(text.splitlines())
    data = text.splitlines()
    
    #Remove Burial Permit
    if data[0].find('Burial') >= 0:
        data.pop(1)
    #Remove first column
    if data[0].find('DAINTY') == -1:
        data.pop(0)
    #Removing
    if data[0].find('_') >= 0:
        data.pop(0)
    #Remove empty list item
    removeEmptyItem(data)
    #Get name
    name = getName(data[0])

    #Iterating and identifying
    index = 0
    for i in data:
        i = i.lower()
        if i.find('oath of') >= 0 or i.find('oate of') >= 0 or i.find('date of') >= 0 or i.find('dati of') >= 0:
            data.pop(index)
        if checkForRelation(i):
            relation = checkForRelation(i)
        if getAddress(i):
            address = getAddress(i)
        if getPincode(i):
            pincode = getPincode(i)
        index = index + 1
        if(getState(i)):
            state = getState(i)

    #Remove empty rows
    data = removeEmpty(data)

    #form json
    # print(name+" : "+relation+" : "+address+" : "+pincode)
    jsonItem = {"NAME":name,"RELATION":relation,"ADDRESS":address,"STATE":state,"PINCODE":pincode}
    finalJson.append(jsonItem)

def removeEmptyItem(data):
    index = 0
    for item in data:
        if len(item) == 0:
            data.pop(index)
        index = index + 1

def getName(col):
    if col.find('NABA') >= 0:
        return 'DAILEY, JAE NABA'
    elif col.find('SARA') >= 0:
        return 'DAILEY, SARA'
    elif col.find('KATHELEEN') >= 0:
        return 'DALAS ,KATHELEEN'
    elif col.find('KATHERINE') >= 0:
        return 'DAINTY, KATHERINE'
    elif col.find('N/A') >= 0:
        return col.replace("N/A", "")
    elif col.find('NA') >= 0:
        return col.replace("NA", "")
    else:
        return col

def checkForRelation(rel):
    if rel.find('sister') >= 0:
        return 'Sister'
    elif rel.find('son') >= 0:
        return 'Son'
    elif rel.find('daughter') >= 0:
        return 'Daughter'
    elif rel.find('mom') >= 0:
        return 'Mom'
    elif rel.find('uncle') >= 0:
        return 'Uncle'
    elif rel.find('father') >= 0:
        return 'Father'
    elif rel.find('wife') >= 0:
        return 'Wife'
    elif rel.find('granddaughter') >= 0:
        return 'GrandDaughter'
    elif rel.find('choni') >= 0:
        return 'Parents'

def getAddress(col):
    col = col.upper()
    if col.find('IL_60637') >= 0:
        return '6253 S. MICHIGAN AVE. IL 60637'
    elif col.find('CHICAGO') >= 0 or col.find('CHGO') >= 0 or col.find('SPRINGS') >= 0 or col.find('HARVEY') >= 0:
        col = col.replace('\u00b0','')
        return col
    elif col.find('PRAIRIE') >= 0:
        return '371 Fourth St,Prairie du Sac, Wis 53578'
    elif col.find('N.Y') >= 0:
        return col
    elif col.find('VALPARISO') >= 0:
        return col
    
def getState(col):
    col = col.upper()
    if col.find('IL_60637') >= 0:
        return 'Illinois'
    elif col.find('CHICAGO') >= 0 or col.find('CHGO') >= 0 or col.find('SPRINGS') >= 0 or col.find('HARVEY') >= 0:
        col = col.replace('\u00b0','')
        return 'Illinois'
    elif col.find('PRAIRIE') >= 0:
        return 'Wisconsin'
    elif col.find('N.Y') >= 0:
        return 'New York'
    elif col.find('VALPARISO') >= 0:
        return 'Indiana'

def getPincode(col):
    col = col.upper()
    if col.find('IL_60637') >= 0:
        return '60637'
    elif col.find('CHICAGO') >= 0 or col.find('CHGO') >= 0 or col.find('SPRINGS') >= 0 or col.find('HARVEY') >= 0:
        return processPin(col)
    elif col.find('PRAIRIE') >= 0:
        return '53578'
    elif col.find('N.Y') >= 0:
        return processPin(col)
    elif col.find('VALPARISO') >= 0:
        return processPin(col)

def processPin(col):
    splitText = col.split(' ')
    for item in splitText:
        if item.isnumeric() and len(item) == 5 and int(item) > int(11264):
            return item
    

def removeEmpty(data):
    index = 0
    for i in data:
        if len(data[index]) == 0:
            data.pop(index)
        index = index + 1
    return data

def convertToCSV(filename):
    with open(filename) as json_file:
        data = json.load(json_file)
    csvData = data
    # Open a file for writing
    data_file = open('final_ocr_data.csv', 'w')
    
    # create the csv writer object
    csv_writer = csv.writer(data_file)
    
    # Counter variable used for writing
    # headers to the CSV file
    count = 0
    for item in csvData:
        if count == 0:
            # Writing headers of CSV file
            header = item.keys()
            csv_writer.writerow(header)
            count += 1
        # Writing data of CSV file
        csv_writer.writerow(item.values())
    data_file.close()

def getZoneDate(file_path):
    image = cv2.imread(file_path)
    x = 700
    y = 120
    w = 120
    h = 50
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pytesseract.image_to_data(rgb, output_type= Output.DICT)
    # loop over each of the individual text localizations
    for i in range(0, len(results["text"])):
        # extract the bounding box coordinates of the text region from
        # the current result
        x = results["left"][i]
        y = results["top"][i]
        w = results["width"][i]
        h = results["height"][i]
        
        # extract the OCR text itself along with the confidence of the
        # text localization
        text = results["text"][i]
        conf = int(results["conf"][i])
        # filter out weak confidence text localizations
        if conf > 60:
            # display the confidence and text to our terminal
            print("Confidence: {}".format(conf))
            print("Text: {}".format(text))
            print("")
            # strip out non-ASCII text so we can draw the text on the image
            # using OpenCV, then draw a bounding box around the text along
            # with the text itself
            text = "".join([c if ord(c) < 128 else "" for c in text]).strip()
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(image, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                1.2, (0, 0, 255), 3)
    # show the output image
    plt.figure()
    plt.imshow(image) 
    plt.show()


def readAll():
    print("-- Processing Images --")
    path = os.getcwd()
    if(path.find('images') < 0):
        os.chdir(path+'/images')
    index = 0
    for file in os.listdir():
        if file.endswith(".png"):
            file_path = f"{path}/{file}"
            ocr(file_path)
    # print(str(finalJson))
    json_file_name = 'final_ocr_data.json'
    with open(json_file_name, 'w') as outfile:
        json.dump(finalJson, outfile)
    print("-- Output saved to system as .json file --")
    print("-- Inserting data into Postgres table --")
    insertData(finalJson)

    convertToCSV(json_file_name)
    print("-- Output saved--")

def readZone():
    print("-- Processing Images --")
    path = os.getcwd()
    if(path.find('images') < 0):
        os.chdir(path+'/images')
    index = 0
    for file in os.listdir():
        if file.endswith(".png"):
            file_path = f"{path}/{file}"
            getZoneDate(file_path)

tableName = 'PERSON'
columns = ['NAME','RELATION','ADDRESS','STATE','PINCODE']

def createDB():
    con = psycopg2.connect(dbname='ocr',user='yoar', host='localhost' ,password='565656')
    cur = con.cursor()
    try:
        cur.execute("CREATE TABLE "+tableName+"(id serial PRIMARY KEY, NAME varchar, RELATION varchar, ADDRESS varchar, STATE varchar, PINCODE integer)")
    except psycopg2.Error:
        cur.close()
        con.close()
        return
    finally:
        con.commit()
        cur.close()
        con.close()
    

def insertData(jsondata):
    con = psycopg2.connect(dbname='ocr',user='yoar', host='localhost' ,password='565656')
    cur = con.cursor()
    for item in jsondata:
        my_data = [item[field] for field in columns]
        for i, v in enumerate(my_data):
            if isinstance(v, dict):
                my_data[i] = json.dumps(v)
        insert_query = "INSERT INTO "+tableName+" (NAME,RELATION,ADDRESS,STATE,PINCODE) VALUES (%s, %s, %s, %s,%s)"
        cur.execute(insert_query, tuple(my_data))
    con.commit()
    cur.close()
    con.close()

    

#Run only the first time if images are in jpg
# convertToPng()

createDB()
#Read image and store as CSV
readAll()

# Experimenting with zonal read
# readZone()