import joblib
import pandas as pd 
import sys
from get_license_plate_data import get_data

def calculate_price(manufacturer, model, year, fuel_type, engine_size, drivetrain, transmission, mileage, seller):
    #Reads dataframe and machinelearning model from a file
    rf = joblib.load('C:\\Users\\Henrikki\\Desktop\\alpr\\Machine learning model\\rfr_model.sav')
    odt = pd.read_csv("C:\\Users\\Henrikki\\Desktop\\alpr\\Machine learning model\\export_dataframe.csv") 

    #Adds data about a wanted car to a dataframe
    odt.loc[:, 'Year'] = year
    odt.loc[:, 'Mileage'] = mileage
    odt.loc[:, 'Engine Size'] = engine_size
    odt.loc[:,  'Model_' + model] = 1
    odt.loc[:,  'Seller_' + seller] = 1
    odt.loc[:,  'Transmission_' + transmission] = 1
    odt.loc[:,  'Manufacturer_' + manufacturer] = 1
    odt.loc[:,  'Drivetrain_' + drivetrain] = 1
    odt.loc[:,  'Fuel type_' + fuel_type] = 1

    try:
        price = int((rf.predict(odt)))
        return(price)
    except:
        print('Maker/Model unknown to database')
        return("-")

def get_car_price(final_plate):
    car_data = []
    car_data = get_data(final_plate)

    if car_data == False:
        return False
    else:
        manufacturer = car_data[0]
        model = car_data[1]
        year = car_data[2]
        fuel_type = car_data[3]
        engine_size = car_data[4]
        drivetrain = car_data[5]
        transmission = car_data[6]
        power = car_data[7]
        cylinder = car_data[8]
        seller = 'Private seller'
        mileage = (2019-int(year))*13000

        price = calculate_price(manufacturer, model, year, fuel_type, engine_size, drivetrain, transmission, mileage, seller)
        return manufacturer, model, year, fuel_type, engine_size, drivetrain, transmission, power, price, cylinder