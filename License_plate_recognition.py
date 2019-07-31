
from __future__ import print_function

import os
import subprocess
import sys
from PIL import Image, ImageDraw, ExifTags, ImageColor
import boto3
import io

#import gphoto2 as gp


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

def crop_and_upload_photo(file, bucket, imgHeight, imgWidth):
    size = imgHeight*0.2, imgWidth*0.2
    infile = file + ".JPG"
    thumbnailphoto = file + "thumbnail.JPG"
    print("tekee thumbnailin")
    if infile != thumbnailphoto:
        try:
            im = Image.open(infile)
            im.thumbnail(size, Image.ANTIALIAS)
            im.save(thumbnailphoto, "JPEG")
        except IOError:
            print ("cannot create thumbnail for '%s'" % infile)
            
    #Lähettää tämän Amazoniin
    print("lähettää Amazoniin")
    #s3 = boto3.client('s3')
    #s3.upload_file(thumbnailphoto, bucket, thumbnailphoto)

    #pip install awscli
    #https://qiita.com/hengsokvisal/items/329924dd9e3f65dd48e7

#ottaa 
def get_car_location(file, bucket):
    #Antaa paluuarvona auton lokaation kuvassa

    thumbnailphoto = file + "thumbnail.JPG"
    client=boto3.client('rekognition')
    print("Connectaa Rekognitioniin")
    """response = client.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':thumbnailphoto}},
        MaxLabels=5)

    print()
    print('Detected labels for ' + thumbnailphoto) 
    print()   
    for label in response['Labels']:
        #print ("Label: " + label['Name'])
        if (label['Name'] == "Car" or label['Name'] == "Vehicle") and int(label['Confidence'] > 90):
            biggest_car_box = 0
            for instance in label['Instances']:
                print("Biggest car box: ", biggest_car_box)
                if float(instance['BoundingBox']['Width']) > biggest_car_box:
                    biggest_car_box = float(instance['BoundingBox']['Width'])
                    height = float(instance['BoundingBox']['Height'])
                    left = float(instance['BoundingBox']['Left'])
                    top = float(instance['BoundingBox']['Top'])
                    width = float(instance['BoundingBox']['Width'])
                    confidence = float(instance['Confidence'])
        else:
            pass
    
    if top > 0:
        print ("    Top: ", top)
        print ("    Left: ", left)
        print ("    Width: ",  width)
        print ("    Height: ",  height)
        print (" Confidence  ", confidence)
    else:
        print("car not found in photo")
    #Tulee vastauksena isoimmain auton kuution mitat
    """
    height = 0.16993412375450134
    left = 0.3946577310562134
    top = 0.5657665133476257
    width = 0.14023849368095398
    car_location = []
    car_location.extend((height, left, top, width))
    return car_location

#Ottaa arvona kuvan auton paikan
def license_plate_recognition(file, bucket, car_location, imgHeight, imgWidth):
    height = imgHeight * car_location[0]
    left = imgWidth * car_location[1]
    top = imgHeight * car_location[2]
    width = imgWidth * car_location[3]

    #Croppaa auton kuvasta parametrien avulla ja lähettää Amazoniin   
    infile = file + ".JPG"
    im = Image.open(infile)
    cropped_photo = file + "cropped.JPG"
    print("Croppaa") 
    
    #Provide the target width and height of the image
    cropped = im.crop( ( left, top, left + width, top + height ) ) 
    cropped.save(cropped_photo, "JPEG")

    #Uppaa kuvan amazonin buckettiin 
    s3 = boto3.client('s3')
    s3.upload_file(cropped_photo, bucket, cropped_photo)
    print("Valmis")
    #Lähettää kuvan tekstintunnistukseen ja saa paluuviestinä rekisterinumeron
    client=boto3.client('rekognition')

    response=client.detect_text(Image={'S3Object':{'Bucket':bucket,'Name':cropped_photo}})
             
    """textDetections=response['TextDetections']
    print ('Detected text')
    for text in textDetections:
            print ('Detected text:' + text['DetectedText'])
            print ('Confidence: ' + "{:.2f}".format(text['Confidence']) + "%")
            print ('Id: {}'.format(text['Id']))
            if 'ParentId' in text:
                print ('Parent Id: {}'.format(text['ParentId']))
            print ('Type:' + text['Type'])
            print
    """
    
    #Seuraavaksi tähän operaatio, joka nappaa noista teksteistä rekkari. Eli confidence yli 80 ja pituus 4 merkkiä tai yli? tai pitää olla viiva? tai jotain. 

def main():
    #muuta bucket ja thumbnailphoto tänne muuttujiksi. Tai bucket ylös vakioksi. 
    photo = "DSC_0061"
    imgHeight = 4000
    imgWidth = 6000
    bucket = 'helanderinkanakori'
    car_location = []
    crop_and_upload_photo(photo, bucket, imgHeight, imgWidth)
    car_location = get_car_location(photo, bucket)
    license_plate_recognition(photo, bucket, car_location, imgHeight, imgWidth)

if __name__ == "__main__":
    sys.exit(main())
