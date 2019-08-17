import os
import subprocess
from PIL import Image, ImageDraw, ExifTags, ImageColor
import boto3
import io
#import gphoto2 as gp

def has_numbers(inputString):
     return any(char.isdigit() for char in inputString)

def has_letters(inputString):
     return any(char.isalpha() for char in inputString)

def convert(list):  
    res = "".join(map(str, list))
    return res 

def license_plate_text_parsing (license_plate):
    if ((len(license_plate) == 6) or (len(license_plate) == 7)) and ("-" in license_plate):
        final_license_plate = (license_plate[:3] + "-" + license_plate[-3:])
    elif (len(license_plate) == 8) and ("-" in license_plate) and (license_plate[-1:] == "1"):
        final_license_plate = (license_plate[:3] + "-" + license_plate[-4:-1])
    else:
        i = 0
        y = 0
        letters = []
        numbers = []
        #Tämä muuttaa mahdolliset 1 ja 0 kirjaimissa I ja O-kirjaimiksi 
        if ((len(license_plate) == 6) or (len(license_plate) == 7)):
            license_plate_letters = license_plate[:3]
            license_plate_letters = license_plate[:3].replace("0","O")
            license_plate_letters = license_plate_letters.replace("1","I")
            license_plate = (license_plate_letters + "-" + license_plate[-3:])
        #Tämä ottaa kirjaimet
        for character in license_plate:
            if (character.isalpha() == False) or (i>2) or (character == "-"):
                break
            letters.append(character)
            i+=1
        #Tämä ottaa numerot
        for number in reversed(license_plate):
            if (number.isdigit() == False) or (y>2) or (number == "-"):
                break
            numbers.append(number)
            y+=1
        numbers = numbers[::-1]
        #Adds letters and numbers together and combines final license plate
        final_license_plate = (convert(letters)+"-"+convert(numbers))
    return final_license_plate

def take_photo():
    #Määrittää kameran
    camera = gp.check_result(gp.gp_camera_new())
    file_path = gp.check_result(gp.gp_camera_capture(
    camera, gp.GP_CAPTURE_IMAGE))
    target = os.path.join('/home/pi/alpr/Rekisterikilvet', file_path.name)
    print('Copying image to', target)
    camera_file = gp.check_result(gp.gp_camera_file_get(
            camera, file_path.folder, file_path.name, gp.GP_FILE_TYPE_NORMAL))
    gp.check_result(gp.gp_file_save(camera_file, target))

def crop_and_upload_photo(photo, bucket, imgHeight, imgWidth):
    ratio = 1600/imgWidth
    print("Ratio:", ratio)
    size = imgHeight*ratio, imgWidth*ratio
    infile = (photo + ".JPG")
    thumbnailphoto = photo + "thumbnail.JPG"
    print("tekee thumbnailin")
    try:
        im = Image.open(infile)
        im.thumbnail(size, Image.ANTIALIAS)
        im.save(thumbnailphoto, "JPEG")
                
        #Lähettää tämän Amazoniin
        print("lähettää Amazoniin")
        s3 = boto3.client('s3')
        s3.upload_file(thumbnailphoto, bucket, thumbnailphoto)
    except:
        print("Can't crop photo")
    #pip install awscli
    #https://qiita.com/hengsokvisal/items/329924dd9e3f65dd48e7

def get_car_location(photo, bucket, car_detection_confidence, car_detection_place):
    thumbnailphoto = photo + "thumbnail.JPG"
    client=boto3.client('rekognition')
    print("Tunnistaa autoa")
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':thumbnailphoto}},MaxLabels=5)
    biggest_car_box = 0

    for label in response['Labels']:
        if ((label['Name'] == "Car") or (label['Name'] == "Vehicle") or (label['Name'] == "Automobile")):
            for instance in label['Instances']:
                confidence = float(instance['Confidence'])
                if float(instance['BoundingBox']['Width']) > biggest_car_box and confidence > car_detection_confidence and float(instance['BoundingBox']['Left']) >= car_detection_place:
                    biggest_car_box = float(instance['BoundingBox']['Width'])
                    height = float(instance['BoundingBox']['Height'])
                    left = float(instance['BoundingBox']['Left'])
                    top = float(instance['BoundingBox']['Top'])
                    width = float(instance['BoundingBox']['Width'])
    if biggest_car_box == 0:
        print("Autoja ei löydetty kuvasta")
        quit()
    else:
        car_location = []
        car_location.extend((height, left, top, width))
        return car_location

#Ottaa arvona kuvan auton paikan
def get_license_plate(photo, bucket, car_location, imgHeight, imgWidth, license_plate_confidence):
    
    height = imgHeight * car_location[0]
    left = imgWidth * car_location[1]
    top = imgHeight * car_location[2]
    width = imgWidth * car_location[3]
    
    #Croppaa auton kuvasta parametrien avulla ja lähettää Amazoniin   
    infile = photo + ".JPG"
    im = Image.open(infile)
    cropped_photo = photo + "cropped.JPG"
    
    #Provide the target width and height of the image
    cropped = im.crop( ( left, top, left + width, top + height ) ) 
    cropped.save(cropped_photo, "JPEG")
    
    #Uppaa kuvan amazonin buckettiin 
    s3 = boto3.client('s3')
    s3.upload_file(cropped_photo, bucket, cropped_photo)
    #Lähettää kuvan tekstintunnistukseen ja saa paluuviestinä rekisterinumeron
    client=boto3.client('rekognition')

    saved_plate = ""
    earlier_confidence = 0

    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':cropped_photo}})
    textDetections=response['TextDetections']
    print("Tunnistaa kilpeä")
    for text in textDetections:
        found_text = (text['DetectedText'])
        if (float(text['Confidence']) > license_plate_confidence and float(text['Confidence']) > earlier_confidence and len(found_text) >= 2 and (has_numbers(found_text) == True) and (has_letters(found_text) == True)):
            saved_plate = found_text
            earlier_confidence = float(text['Confidence'])
    if saved_plate != "":
        final_license_plate = license_plate_text_parsing(saved_plate)
        print("License plate: ", final_license_plate)
        return final_license_plate
    else:
        print("Kilpiä ei tunnistettu kuvasta")
        return saved_plate

def delete_photos(photo, bucket):
    cropped_photo = photo + "cropped.JPG"
    thumbnailphoto = photo + "thumbnail.JPG"
    s3 = boto3.client('s3')
    s3.delete_object(Bucket=bucket, Key=thumbnailphoto)
    s3.delete_object(Bucket=bucket, Key=cropped_photo)
    print("Kuvat poistettu pilvestä")


license_plate_text_parsing("L0E:236")