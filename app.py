#!/usr/bin/python3

from flask import Flask
from flask import render_template
from flask_restful import Resource, Api, fields, marshal_with, reqparse
# logging facility: https://realpython.com/python-logging/
import logging

# sqlite3 access API
import sqlite3
from sqlite3 import Error
import datetime

app = Flask(__name__)
api = Api(app)
parser = reqparse.RequestParser()

dbfilename = "/opt/thermo/data.db"

resourceFields = {
    'id':       fields.Integer,
    'sensorid': fields.Integer,
    'date':     fields.String,
    'time':     fields.String,
    'isodatetime': fields.String,
    'value':    fields.Float
}

# create connection to our db
def createConnection(dbFileName):
    """ create a database connection to a SQLite database """
    try:
        db = sqlite3.connect(dbFileName)
        return db
    except Error as e:
        logging.error("Unable to create database connection to %s", dbFileName)
        db.close()

    return None

# get number of rows in table
def countRows(mydb):
    sql = '''select count(*) from datapoints'''
    try:
        cursor = mydb.cursor()
        result = cursor.execute(sql).fetchone()
        return result[0]

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get row count of table datapoints")

        return 0


# get specific row
def getRow(mydb, id):
    try:
        cursor = mydb.cursor()
        cursor.execute('''SELECT * FROM datapoints WHERE id=?''', (id,))
        return cursor.fetchone()

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get data point %s", id)

        return 0


# get specific row
def getRows(mydb, fromId, toId):
    try:
        cursor = mydb.cursor()
        cursor.execute('''SELECT * FROM datapoints WHERE id>=? and id<=?''', (fromId, toId,))
        return cursor.fetchall()

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get data point %s", id)

        return 0

# get the last data point for a given sensor
def getLastRowForSensor(sensorId):
    try:
        logging.info("Get last data point for sensor %s", sensorId)
        mydb = createConnection(dbfilename)
        cursor = mydb.cursor()
        sql = '''select count(*) from datapoints'''
        result = cursor.execute(sql).fetchone()
        lastRow = result[0]
        cursor.execute('''SELECT * FROM datapoints WHERE sensorid=? and id>=? and id<=?''', (sensorId, lastRow - 2, lastRow,))
        row = cursor.fetchone()
        mydb.close()
        return row

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get data point %s", id)

    mydb.close()
    return None

# get specific row
def getLastNRowsBySensor(sensorId, rowCount):
    try:
        logging.info("Get last %s data points for sensor %s", rowCount, sensorId)
        mydb = createConnection(dbfilename)
        cursor = mydb.cursor()
        sql = '''select count(*) from datapoints'''
        result = cursor.execute(sql).fetchone()
        lastRow = result[0]
        cursor.execute('''SELECT * FROM datapoints WHERE sensorid=? and id>=? and id<=?''',
                       (sensorId, lastRow - (3 * rowCount), lastRow,))
        row = cursor.fetchall()
        mydb.close()
        return row

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get data point %s", id)

    mydb.close()
    return None


# get all data points for a given sensor
def getAllRowsForSensor(sensorId):
    try:
        logging.info("Get last data point for sensor %s", sensorId)
        mydb = createConnection(dbfilename)
        cursor = mydb.cursor()
        sql = '''select count(*) from datapoints'''
        result = cursor.execute(sql).fetchone()
        lastRow = result[0]
        cursor.execute('''SELECT * FROM datapoints WHERE sensorid=? order by id''', (sensorId,))
        rows = cursor.fetchall()
        mydb.close()
        return rows

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get data point %s", id)

    mydb.close()
    return None

# get all data points for a given sensor
def getAllRowsBySensorByDate(sensorId, date):
    try:
        logging.info("Get all data points for sensor %s and %s", sensorId, date)
        mydb = createConnection(dbfilename)
        cursor = mydb.cursor()
        sql = '''select count(*) from datapoints'''
        result = cursor.execute(sql).fetchone()
        lastRow = result[0]
        cursor.execute('''SELECT * FROM datapoints WHERE sensorid=? and date=? order by id''', (sensorId, date,))
        rows = cursor.fetchall()
        mydb.close()
        return rows

    except Error as e:
        logging.exception("Exception occurred")
        logging.error("Unable to get data point %s", id)

    mydb.close()
    return None


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/current')
def current():
    return render_template('current.html')

@app.route('/todaychart')
def todaychart():
    return render_template('todaychart.html')

@app.route('/log')
def log():
    f = open("/tmp/thermo.log", "r")

    page = "<!DOCTYPE html>"
    page = page + "<html><h1>Web Thermometer Sensor Reader Log</h1><hr><br><pre>"

    for line in f:
        page = page + line

    page = page + "</pre></html>"
    return page


@app.route('/summary')
def summary():
    page = "<!DOCTYPE html>"
    page = page + "<html><h1>Web Thermometer Sensor Summary</h1><hr><br>"

    db = createConnection(dbfilename)
    rowCount = countRows(db)
    page = page + "Number of data points in table: " + str(rowCount) + '<p>'
    row = getRow(db, rowCount)

    rows = getRows(db, rowCount - 24, rowCount)
    page = page + "Last 24 rows: <p>"
    for r in rows:
        page = page + str(r) + '<p>'

    page = page + "Last data point: " + str(row) + '<p>'
    db.close()

    page = page + "</html>"
    return page


class DataPointDAO(object):
    def __init__(self, row):
        self.id = row[0]
        self.sensorid =row[1]
        self.date = row[2]
        self.time = row[3]
        self.isodatetime = row[4]
        self.value = row[5]

class DataPoint(Resource):
    @marshal_with(resourceFields)
    def get(self, sensorid):
        row = getLastRowForSensor(sensorid)
        return DataPointDAO(row)


class DataPoints(Resource):
    @marshal_with(resourceFields)
    def get(self, sensorid):
        rows = getAllRowsForSensor(sensorid)
        dataPoints = []
        for row in rows:
            dataPoints.append(DataPointDAO(row))
        return dataPoints

class DataPointsToday(Resource):
    @marshal_with(resourceFields)
    def get(self, sensorid):
        now = datetime.datetime.now()
        nowDate = now.strftime("%Y-%m-%d")
        rows = getAllRowsBySensorByDate(sensorid, nowDate)
        dataPoints = []
        for row in rows:
            dataPoints.append(DataPointDAO(row))
        return dataPoints

class DataPointsLastN(Resource):
    @marshal_with(resourceFields)
    def get(self, sensorid, numberRows):
        rows = getLastNRowsBySensor(sensorid, numberRows)
        dataPoints = []
        for row in rows:
            dataPoints.append(DataPointDAO(row))
        return dataPoints

# set up the logger
#logging.basicConfig(filename="/tmp/thermowebapp.log", format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)

#api.add_resource(DataPoint, '/datapoint')
api.add_resource(DataPoint, '/datapoint/<int:sensorid>')
api.add_resource(DataPoints, '/datapoints/<int:sensorid>')
api.add_resource(DataPointsToday, '/datapoints/today/<int:sensorid>')
api.add_resource(DataPointsLastN, '/datapoints/<int:sensorid>/<int:numberRows>')

if __name__ == '__main__':
    db = createConnection(dbfilename)
    app.run(debug=True, host='0.0.0.0')

