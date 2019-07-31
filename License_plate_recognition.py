
from __future__ import print_function

import os
import subprocess
import sys
from PIL import Image, ImageDraw, ExifTags, ImageColor
import boto3
import io

#import gphoto2 as gp


def has_numbers(inputString):
     return any(char.isdigit() for char in inputString)

def has_letters(inputString):
     return any(char.isalpha() for char in inputString)

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
    size = imgHeight*0.2, imgWidth*0.2
    infile = (photo + ".JPG")
    thumbnailphoto = photo + "thumbnail.JPG"
    print("tekee thumbnailin")
    im = Image.open(infile)
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(thumbnailphoto, "JPEG")
            
    #Lähettää tämän Amazoniin
    print("lähettää Amazoniin")
    s3 = boto3.client('s3')
    s3.upload_file(thumbnailphoto, bucket, thumbnailphoto)

    #pip install awscli
    #https://qiita.com/hengsokvisal/items/329924dd9e3f65dd48e7

#ottaa 
def get_car_location(file, bucket):
    #Antaa paluuarvona auton lokaation kuvassa

    thumbnailphoto = file + "thumbnail.JPG"
    client=boto3.client('rekognition')
    print("Tunnistaa autoa")
    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':thumbnailphoto}},
        MaxLabels=5)

    for label in response['Labels']:
        if ((label['Name'] == "Car") or (label['Name'] == "Vehicle")):
            biggest_car_box = 0
            for instance in label['Instances']:
                confidence = float(instance['Confidence'])
                print("Auton tunnistus tarkkuus: ", confidence)
                if float(instance['BoundingBox']['Width']) > biggest_car_box and confidence > 83:
                    biggest_car_box = float(instance['BoundingBox']['Width'])
                    print("Biggest car box: ", biggest_car_box)
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
def license_plate_recognition(photo, bucket, car_location, imgHeight, imgWidth, license_plate_confidence):
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

    saved_texts = []

    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':cropped_photo}})
    textDetections=response['TextDetections']
    print("Tunnistaa kilpeä")
    for text in textDetections:
        found_text = (text['DetectedText'])
        print(found_text, " Confidence: ", float(text['Confidence']))
        if (float(text['Confidence']) > license_plate_confidence and len(found_text) >= 2 and (has_numbers(found_text) == True) and (has_letters(found_text) == True)):
            saved_texts.append(found_text)
    if len(saved_texts) > 0:
        license_plate_text = saved_texts[0]
        print(license_plate_text)
    else:
        print("Kilpiä ei tunnistettu kuvasta")
    #Tähän vielä sellanne, että lähtee oikealta liikkeelle ja kun törmää ekaan kirjaimeen niin laittaa väliviivan ennen sitä, jollei jo ole sanassa. Myös sen jälkeen muuttaa numeropuolen ykköset kirjaimiksi etc.
    #Lähtee vasemmalta ja ottaa kolme ensimmäistä kirjainta
    #Seuraavaksi tähän operaatio, joka poistaa kuvat bucketista.
    #Sellanen vielä, että osaa ottaa molemmat autot. Ei vaikka pelkästään yhtä, jos tarkkuus tietenkin riittävä. 

def main():
    #muuta bucket ja thumbnailphoto tänne muuttujiksi. Tai bucket ylös vakioksi. 
    photo = "c:\\Users\\Henrikki\\Downloads\\Licenseplaterecog\\Rekisterikilvet\\DSC_0050"
    imgHeight = 4000
    imgWidth = 6000
    bucket = 'helanderinkanakori'
    license_plate_confidence = 80 #Kuinka monta prosenttia suurempi varmuuden pitää olla, että kilpi hyväksytään. Eli nyt tunnistetaan teksti > 80% varmuudella. 
    car_location = []
    crop_and_upload_photo(photo, bucket, imgHeight, imgWidth)
    car_location = get_car_location(photo, bucket)
    license_plate_recognition(photo, bucket, car_location, imgHeight, imgWidth, license_plate_confidence)

if __name__ == "__main__":
    sys.exit(main())
