from tkinter import Label, Button, StringVar, Tk, mainloop
from license_plate_recognition import get_car_location, get_license_plate, delete_photos, crop_and_upload_photo
from price_predictor import get_car_price
from PIL import Image

master = Tk()

def change_values():
    photo = "C:\\Users\\Henrikki\\Desktop\\alpr\\Rekisterikilvet\\bmw"
    im = Image.open(photo + ".jpg")
    imgWidth, imgHeight = im.size
    bucket = 'helanderinkanakori'
    license_plate_confidence = 80 #Kuinka monta prosenttia suurempi varmuuden pitää olla, että kilpi hyväksytään. Eli nyt tunnistetaan > 80% varmuudella. 
    car_detection_confidence = 70 #Auton tunnistamisen varmuus
    car_detection_place = 0.00 #Kuinka monta % auto on vasemmasta laidasta. Eli 0,5 = auto sijaitsee kuvan keskiosion oikealla puolella. 
    car_location = []
    car_data = []

    crop_and_upload_photo(photo, bucket, imgHeight, imgWidth)
    car_location = get_car_location(photo, bucket, car_detection_confidence, car_detection_place)
    final_plate = get_license_plate(photo, bucket, car_location, imgHeight, imgWidth, license_plate_confidence)
    delete_photos(photo, bucket)
    car_data = get_car_price(final_plate)

    if car_data == False:
        manufacturer.set("Rekisterinumeroa ei tunnistettu/löytynyt tietokannasta")
    else:
        manufacturer.set("Merkki: " + car_data[0])
        model.set("Malli: " + car_data[1])
        year.set("Vuosimalli: " + car_data[2])
        fuel_type.set("Polttoaine: " + car_data[3])
        engine_size.set("Moottori: " + car_data[4] + " litraa " + car_data[9] + " sylinteriä")
        drivetrain.set("Vetotapa: " + car_data[5])
        transmission.set("Vaihteisto: " + car_data[6])
        power.set("Teho: " + car_data[7] + " Hp")
        price.set("Arvo: " + str(car_data[8]) + " Euroa")

manufacturer = StringVar()
model = StringVar()
year = StringVar()
fuel_type = StringVar()
engine_size = StringVar()
drivetrain = StringVar()
transmission = StringVar()
power = StringVar()
price = StringVar()

master.minsize(width=400, height=400)
Label(master, textvariable=manufacturer).pack() 
Label(master, textvariable=model).pack()    
Label(master, textvariable=year).pack()
Label(master, textvariable=power).pack() 
Label(master, textvariable=price).pack() 
Label(master, textvariable=engine_size).pack()  
Label(master, textvariable=fuel_type).pack()
Label(master, textvariable=drivetrain).pack()   
Label(master, textvariable=transmission).pack()  


b = Button(master, text="Hae auton tiedot", command=change_values)
b.pack()
mainloop()