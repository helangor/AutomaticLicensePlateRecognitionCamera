from __future__ import print_function
import os
import subprocess
import sys
from PIL import Image, ImageDraw, ExifTags, ImageColor
import boto3
import io
from price_predictor import get_car_data
#import gphoto2 as gp

def has_numbers(inputString):
     return any(char.isdigit() for char in inputString)

def has_letters(inputString):
     return any(char.isalpha() for char in inputString)

def convert(list):  
    res = "".join(map(str, list))
    return res 

#Muokkaa kilven kirjoitusasun oikeaksi.

#YGE-9441
#Tämä kilpi oikeaksi. 
def license_plate_text_parsing (license_plate):
    if (len(license_plate) >= 7) and ("-" in license_plate):
        final_license_plate = (license_plate[:3] + "-" + license_plate[-3:])
        print(final_license_plate)
    else:
        i = 0
        y = 0
        letters = []
        numbers = []
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
            i+=1
        numbers = numbers[::-1]
        #Adds letters and numbers together and combines final license plate
        final_license_plate = (convert(letters)+"-"+convert(numbers))
        print(final_license_plate)
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

def crop_and_upload_photo(photo, bucket, imgHeight, imgWidth, thumbnailphoto):
    size = imgHeight*0.2, imgWidth*0.2
    infile = (photo + ".JPG")
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
def get_car_location(file, bucket, thumbnailphoto):
    #Antaa paluuarvona auton lokaation kuvassa
    client=boto3.client('rekognition')
    print("Tunnistaa autoa")

    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':thumbnailphoto}},MaxLabels=5)
    biggest_car_box = 0

    for label in response['Labels']:
        #print("label: ", label)
        if ((label['Name'] == "Car") or (label['Name'] == "Vehicle") or (label['Name'] == "Automobile")):
            for instance in label['Instances']:
                confidence = float(instance['Confidence'])
                #print("Auton tunnistus tarkkuus: ", confidence)
                if float(instance['BoundingBox']['Width']) > biggest_car_box and confidence > 83:
                    biggest_car_box = float(instance['BoundingBox']['Width'])
                    #print("Biggest car box: ", biggest_car_box)
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
        license_plate = saved_texts[0]
        final_license_plate = license_plate_text_parsing(license_plate)
        return final_license_plate
    else:
        print("Kilpiä ei tunnistettu kuvasta")

def main():
    #muuta bucket ja thumbnailphoto tänne muuttujiksi. Tai bucket ylös vakioksi. 
    photo = "C:\\Users\\Henrikki\\Desktop\\alpr\\Rekisterikilvet\\DSC_0043"
    thumbnailphoto = photo + "thumbnail.JPG"
    imgHeight = 4000
    imgWidth = 6000
    bucket = 'helanderinkanakori'
    license_plate_confidence = 80 #Kuinka monta prosenttia suurempi varmuuden pitää olla, että kilpi hyväksytään. Eli nyt tunnistetaan teksti > 80% varmuudella. 
    car_location = []

    crop_and_upload_photo(photo, bucket, imgHeight, imgWidth, thumbnailphoto)
    car_location = get_car_location(photo, bucket, thumbnailphoto)
    final_plate = license_plate_recognition(photo, bucket, car_location, imgHeight, imgWidth, license_plate_confidence)
    get_car_data(final_plate)

    #Seuraavaksi tähän operaatio, joka poistaa kuvat bucketista.
    #YGE-9441
    #Tämä kilpi oikeaksi. 

    #Sellanen vielä, että osaa ottaa molemmat autot. Ei vaikka pelkästään yhtä, jos tarkkuus tietenkin riittävä. 

if __name__ == "__main__":
    sys.exit(main())
