from tkinter import *
from license_plate_recognition import crop_and_upload_photo, get_car_location, license_plate_recognition
from price_predictor import get_car_data
master = Tk()

def change_values():
    photo = "C:\\Users\\Henrikki\\Desktop\\alpr\\Rekisterikilvet\\DSC_0057"
    thumbnailphoto = photo + "thumbnail.JPG"
    imgHeight = 4000
    imgWidth = 6000
    bucket = 'helanderinkanakori'
    license_plate_confidence = 80 #Kuinka monta prosenttia suurempi varmuuden pitää olla, että kilpi hyväksytään. Eli nyt tunnistetaan > 80% varmuudella. 
    car_location = []
    car_data = []

    crop_and_upload_photo(photo, bucket, imgHeight, imgWidth, thumbnailphoto)
    car_location = get_car_location(photo, bucket, thumbnailphoto)
    final_plate = license_plate_recognition(photo, bucket, car_location, imgHeight, imgWidth, license_plate_confidence)
    car_data = get_car_data(final_plate)

    manufacturer.set("Merkki: " + car_data[0])
    model.set("Malli: " + car_data[1])
    year.set("Vuosimalli: " + car_data[2])
    fuel_type.set("Polttoaine: " + car_data[3])
    engine_size.set("Moottorin tilavuus: " + car_data[4])
    drivetrain.set("Vetotapa: " + car_data[5])
    transmission.set("Vaihteisto: " + car_data[6])
    power.set("Teho: " + car_data[7])
    price.set("Hinta: " + str(car_data[8]))


manufacturer = StringVar()
manufacturer.set("")
model = StringVar()
model.set("")
year = StringVar()
year.set("")
fuel_type = StringVar()
fuel_type.set("")
engine_size = StringVar()
engine_size.set("")
drivetrain = StringVar()
drivetrain.set("")
transmission = StringVar()
transmission.set("")
power = StringVar()
power.set("")
price = StringVar()
price.set("")

master.minsize(width=400, height=400)
Label(master, textvariable=manufacturer).pack() 
Label(master, textvariable=model).pack()    
Label(master, textvariable=year).pack()
Label(master, textvariable=fuel_type).pack()
Label(master, textvariable=engine_size).pack()  
Label(master, textvariable=drivetrain).pack()   
Label(master, textvariable=transmission).pack()  
Label(master, textvariable=power).pack() 
Label(master, textvariable=price).pack() 
b = Button(master, text="Hae auton tiedot", command=change_values)
b.pack()
mainloop()


