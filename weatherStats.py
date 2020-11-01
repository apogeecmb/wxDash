import math, time, copy
import sqlite3
import matplotlib.pyplot as plt
import datetime
from calendar import monthrange
import numpy as np
from enum import IntEnum
from threading import Thread

def capitalizeFirst(strIn):
    return strIn[0].upper() + strIn[1:]

class PlotStep(IntEnum):
    ALL = 1
    HOURLY = 2
    DAILY = 3
    WEEKLY = 4
    MONTHLY = 5
    ANNUALLY = 6

class CalcType(IntEnum):
    MIN = 1
    MAX = 2
    AVG = 3
    SUM = 4
    STATS = 5

class DataCalculation():
    def __init__(self, calcType):
        self.calcType = calcType
        if (self.calcType == CalcType.MIN):
            self.calc = 1e20 # initialize to large value
        elif (self.calcType == CalcType.MAX):
            self.calc = -1e20 # initialize to small value
        else:
            self.calc = 0

        self.numPts = 0

    def update(self, value):
        # Update calculation based on type        
        if (self.calcType == CalcType.MIN):
            if (value < self.calc):
                self.calc = value
        elif (self.calcType == CalcType.MAX):
            if (value > self.calc):
                self.calc = value
        elif (self.calcType == CalcType.AVG):
            if (self.numPts > 0):
                self.numPts += 1
                self.calc = self.calc + (value - self.calc) / self.numPts
            else: # first point
                self.calc = value
                self.numPts += 1
        elif (self.calcType == CalcType.SUM):
            self.calc += value

class WeatherPlotter:
    def __init__(self, dbPath, units, plotStyle=None):
        self.dbPath = dbPath
        self.units = units
        
        # Plot style
        if (plotStyle):
            plt.style.use(plotStyle)

        # Open database
        #conn = sqlite3.connect(dbPath)
        #self.dbCursor = conn.cursor()

        # Current weather
        self.currentConditions = dict()

    def getFromDatabase(self, dbRequest):
        conn = sqlite3.connect(self.dbPath)
        dbCursor = conn.cursor()
        dbCursor.execute(dbRequest)
        dataTable = dbCursor.fetchall()

        conn.close()

        return dataTable
        

    def getCurrentWeather(self):

        # Get current weather
        dataTable = self.getFromDatabase('SELECT dateTime, outTemp, outHumidity, windSpeed, windDir, windGust, rain, rainRate FROM archive ORDER BY dateTime DESC LIMIT 1')
        dataEntry = dataTable[0]
        self.currentConditions['time'] = datetime.datetime.fromtimestamp(dataEntry[0])    
    
        # Temperature (max, min, current)
        tempTable = self.getFromDatabase('SELECT dateTime, min, max FROM archive_day_outTemp ORDER BY dateTime DESC LIMIT 1')
        self.currentConditions['outTemp'] = {'current': dataEntry[1], 'min': tempTable[0][1], 'max': tempTable[0][2]}

        # Humidity
        self.currentConditions['humidity'] = dataEntry[2]    

        # Precipitation Total and Rate
        rainTable = self.getFromDatabase('SELECT dateTime, sum FROM archive_day_rain ORDER BY dateTime DESC LIMIT 1')
        self.currentConditions['rain'] = {'sum': rainTable[0][1], 'rainRate': dataEntry[7]}

        # Wind Speed, Direction, and Gust
        self.getFromDatabase('SELECT dateTime, outTemp, outHumidity, windSpeed, windDir, windGust, rain, rainRate FROM archive ORDER BY dateTime DESC LIMIT 1')
        self.currentConditions['wind'] = {'speed': dataEntry[3], 'dir': dataEntry[4], 'gust': dataEntry[5]}

        return self.currentConditions

    def calcPlotData(self, startTime, endTime, timeStep, dataArray, calcType, steps=[]):
        # Calculate data at each step
        if (steps):
            numSteps = len(steps) # last step is end time
        else: # calculate steps
            currentTime = startTime
            numSteps = math.ceil((endTime - startTime) / timeStep)
            stepEnd = currentTime
    
        times = [0]*numSteps
        valuePerStep = np.zeros(numSteps)
        tablePos = 0
        noDataSteps = []
        for i in range(numSteps):
            # Calculate value for this step
            if (steps): # steps provided
                stepStart = steps[i]
                try:
                    stepEnd = steps[i+1]
                except IndexError: # last sep
                    stepEnd = endTime
            else: # calculate step end
                stepStart = stepEnd # start is previous end time
                stepEnd = currentTime + timeStep
            if (stepEnd > endTime):
                stepEnd = endTime
                
            stepCalc = None
            try:
                while (dataArray[tablePos,0] < stepEnd):
                    if (stepCalc == None):
                        stepCalc = DataCalculation(calcType) # calculation at this step
                    stepCalc.update(dataArray[tablePos, 1])
                    tablePos += 1
            except IndexError: # end of data
                pass
                    
            currentTime = stepEnd 
            if (stepCalc): # add data point
                times[i] = datetime.datetime.fromtimestamp(stepStart).strftime("%Y-%m-%d %H:%M")
                valuePerStep[i] = stepCalc.calc
            else: # no data available
                noDataSteps.append(i)
        
        # Remove any empty data steps
        noDataSteps.sort(reverse=True)
        for step in noDataSteps:
            del times[step]
            valuePerStep = np.delete(valuePerStep, step)

        return times, valuePerStep

    def getTempPlotData(self, startTime, endTime, step):
        # Create a plot with min, max, and average temps for desired time span and step
        minTime, minData = getData('outTemp', startTime, endTime, step, CalcType.MIN) # max
        minType = ['min'] * len(minTime)
        maxTime, maxData = getData('outTemp', startTime, endTime, step, CalcType.MAX) # min
        maxType = ['max'] * len(maxTime)
        avgTime, avgData = getData('outTemp', startTime, endTime, step, CalcType.AVG) # avg
        avgType = ['avg'] * len(avgTime)
            
        # Combine data
        allTime = np.concatenate((minTime, maxTime, avgTime), axis=0)
        allData = np.concatenate((minData, maxData, avgData), axis=0)
        allType = np.concatenate((minType, maxType, avgType), axis=0)

        return allTime, allData, allType

    def createTempPlot(self, startTime, endTime, step):
        # Create a plot with min, max, and average temps for desired time span and step
        fig, ax = plt.subplots()
        fig.set_tight_layout(True)

        ax = weatherPlot.createDataPlot('outTemp', startTime, endTime, PlotStep.MONTHLY, CalcType.MIN, ax=ax) # max
        ax = weatherPlot.createDataPlot('outTemp', startTime, endTime, PlotStep.MONTHLY, CalcType.MAX, ax=ax) # min
        ax = weatherPlot.createDataPlot('outTemp', startTime, endTime, PlotStep.MONTHLY, CalcType.AVG, ax=ax) # avg
    
        ax.set_title("Temperature Summary Plot - {} - {} to {}".format(step.name.capitalize(), startTime.strftime("%Y-%m-%d %H:%M"), endTime.strftime("%Y-%m-%d %H:%M")))
   
    def getAvg(self, entry, tableName, startTimeEpoch, endTimeEpoch):
        # Get min and max and average
        if ("day" in tableName):
            minTable = self.getFromDatabase('SELECT dateTime, {} FROM {} WHERE dateTime between {} AND {}'.format(CalcType.MIN.name, tableName, startTimeEpoch, endTimeEpoch))
            maxTable = self.getFromDatabase('SELECT dateTime, {} FROM {} WHERE dateTime between {} AND {}'.format(CalcType.MAX.name, tableName, startTimeEpoch, endTimeEpoch))
                
            dataArray = np.array(minTable)
            for i in range(len(maxTable)):
                dataArray[i,1] = (minTable[i][1] + maxTable[i][1]) / 2.0

        else: # return all points
            dataTable = self.getFromDatabase('SELECT dateTime, {} FROM {} WHERE dateTime between {} AND {}'.format(entry, tableName, startTimeEpoch, endTimeEpoch))
            dataArray = np.array(dataTable)


        return dataArray
          
    def getData(self, entry, startTime, endTime, step, calcType=CalcType.MAX):
        startTimeEpoch = datetime.datetime.timestamp(startTime)
        endTimeEpoch = datetime.datetime.timestamp(endTime)
        
        dataArray = None
        tableName = None
        times = None
        values = None
        steps = []
    
        # Get requested data for requested step
        if (step == PlotStep.ALL): # return all points in main database table
            tableName = "archive"
            timeStep = "all"
            databaseEntry = entry
            
        elif (step == PlotStep.HOURLY):
            tableName = "archive"
            databaseEntry = entry
            timeStep = 3600.0

        elif (step == PlotStep.DAILY): # daily data is already included in database
            tableName = "archive_day_{}".format(entry)
            timeStep = 86400.0
            databaseEntry = calcType.name

        elif (step == PlotStep.WEEKLY):
            tableName = "archive_day_{}".format(entry)
            timeStep = 86400.0 * 7
            databaseEntry = calcType.name
        
        elif (step == PlotStep.MONTHLY):
            tableName = "archive_day_{}".format(entry)
            timeStep = 86400.0 * 7 * 30
            databaseEntry = calcType.name
            # Generate start of month times
            steps = [startTime]
            while (steps[-1] + datetime.timedelta(days=monthrange(steps[-1].year, steps[-1].month)[1]) < endTime):
                month = steps[-1].month + 1
                year = steps[-1].year
        
                if (month > 12): # Check for end of year
                    month = 1
                    year = steps[-1].year + 1

                steps.append(datetime.datetime(year, month, 1))
            steps = [datetime.datetime.timestamp(dt) for dt in steps]
        
        elif (step == PlotStep.ANNUALLY):
            tableName = "archive_day_{}".format(entry)
            timeStep = 86400.0 * 7 * 365
            databaseEntry = calcType.name
            # Generate start of year times
            steps = [startTime]
            while (datetime.datetime(steps[-1].year + 1, 1, 1) < endTime):
                steps.append(datetime.datetime(steps[-1].year + 1, 1, 1))
        
            steps = [datetime.datetime.timestamp(dt) for dt in steps]
        
        # Check calculation type
        if (calcType == CalcType.AVG):
            dataArray = self.getAvg(entry, tableName, startTimeEpoch, endTimeEpoch)
        else:
            #dataTable = self.getFromDatabase('SELECT dateTime, {} FROM archive WHERE dateTime between {} AND {}'.format(entry, startTimeEpoch, endTimeEpoch))
            dataTable = self.getFromDatabase('SELECT dateTime, {} FROM {} WHERE dateTime between {} AND {}'.format(databaseEntry, tableName, startTimeEpoch, endTimeEpoch))
            dataArray = np.array(dataTable)

        # Check if plot data needs to be calculated
        if (dataArray is not None):
            if (timeStep == 'all'):
                times = [datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M") for t in dataArray[:,0]]
                values = dataArray[:,1]
            else: # calculate values for each time step
                times, values = self.calcPlotData(startTimeEpoch, endTimeEpoch, timeStep, dataArray, calcType, steps)
        return times, values

    def createDataPlot(self, entry, startTime, endTime, step, calcType=CalcType.MAX, ax=None):
        startTimeEpoch = datetime.datetime.timestamp(startTime)
        endTimeEpoch = datetime.datetime.timestamp(endTime)
    
        # Get axes
        if (ax == None):
            fig, ax = plt.subplots()
            fig.set_tight_layout(True)

        x, y = self.getData(entry, startTime, endTime, step, calcType)

        ax.plot(x, y, '.')

        # Format plot    
        ax.tick_params(axis='x', rotation=75)
        ax.set_title("{} of {} - {} - {} to {}".format(calcType.name.capitalize(), capitalizeFirst(entry), step.name.capitalize(), startTime.strftime("%Y-%m-%d %H:%M"), endTime.strftime("%Y-%m-%d %H:%M")))
        ax.set_xlabel("Time")
        ax.set_ylabel("{} ({})".format(capitalizeFirst(entry), self.units[entry]))

        return ax

    def getPlotData(self, plotRequest):
        dataOut = None

        if (plotRequest['type'] == 'tempPlot'):
            dates, data, types = self.getTempPlotData(plotRequest['startTime'], plotRequest['endTime'], plotRequest['plotStep'])
            dataRequest = copy.deepcopy(plotRequest)
            dataRequest['dates'] = dates
            dataRequest['data'] = data
            dataRequest['types'] = types
            dataOut = dataRequest 
        else:
            dates, data = self.getData(plotRequest['data_type'], plotRequest['startTime'], plotRequest['endTime'], plotRequest['plotStep'], plotRequest['calcType'])
            dataRequest = copy.deepcopy(plotRequest)
            dataRequest.update({'type': 'standard', 'dates': dates, 'data': data})
            dataOut = dataRequest 

        return dataOut


class WeatherPlotThread(Thread):
   
    def __init__(self, weatherPlotter, inQueue, outQueue):
        super().__init__()

        # WeatherPlotter object
        self.weatherPlot = weatherPlotter

        # Message queues
        self.inQueue = inQueue
        self.outQueue = outQueue

        self.stopThread = False

    def run(self):
        # Open database connection
        #conn = sqlite3.connect(self.weatherPlot.dbPath)
        #self.weatherPlot.dbCursor = conn.cursor()

        curCondCheckInt = 30.0 # seconds
        lastCurCondCheck = 0.0
        while (self.stopThread == False):
            dataOut = {'current': None, 'dataRequest': None}
            # Check for incoming plot requests
            if (self.inQueue.empty() == False):
                plotRequest = self.inQueue.get()
                if (plotRequest['type'] == 'tempPlot'):
                    dates, data, types = self.weatherPlot.getTempPlotData(plotRequest['startTime'], plotRequest['endTime'], plotRequest['plotStep'])
                    dataRequest = copy.deepcopy(plotRequest)
                    dataRequest['dates'] = dates
                    dataRequest['data'] = data
                    dataRequest['types'] = types
                    dataOut['dataRequest'] = dataRequest 
                else:
                    dates, data = self.weatherPlot.getData(plotRequest['data_type'], plotRequest['startTime'], plotRequest['endTime'], plotRequest['plotStep'], plotRequest['calcType'])
                    dataRequest = copy.deepcopy(plotRequest)
                    dataRequest.update({'type': 'standard', 'dates': dates, 'data': data})
                    dataOut['dataRequest'] = dataRequest 
                    
            # Get current conditions
            #if (time.time() > (lastCurCondCheck + curCondCheckInt)): 
            #    dataOut['current'] = self.weatherPlot.getCurrentWeather() 
            #    lastCurCondCheck = time.time()       
 
            # Output plot request data
            #if (dataOut['current'] != None or dataOut['dataRequest'] != None):
            if (dataOut['dataRequest'] != None):
                self.outQueue.put(dataOut)


            time.sleep(1.0)


if (__name__ == '__main__'):
    path = "/home/weewx/archive/weewx.sdb" 

    # Create plotter
    units = {"outTemp": "deg F", "rain": "in", "rainRate": "in/hr"}
    weatherPlot = WeatherPlotter(path, units, "plot_style.mplstyle")

    weatherPlot.getCurrentWeather()
    ## Graphs

    # Rain for hour - all timesteps available
    startTime = datetime.datetime(2020, 8, 26, 7)
    endTime = datetime.datetime(2020, 8, 26, 8)
    weatherPlot.createDataPlot('rain',  startTime, endTime, PlotStep.ALL, CalcType.SUM)
    plt.show()

    # Rain for day - hourly steps
    startTime = datetime.datetime(2020, 8, 26, 0)
    endTime = datetime.datetime(2020, 8, 27, 1)
    weatherPlot.createDataPlot('rain', startTime, endTime, PlotStep.HOURLY, CalcType.SUM)
    plt.show()

    # Rain for month - day steps
    startTime = datetime.datetime(2020, 9, 1)
    endTime = datetime.datetime(2020, 10, 1)
    ax = weatherPlot.createDataPlot('rain', startTime, endTime, PlotStep.DAILY, CalcType.SUM)
    plt.show()

    # Rain in week steps
    startTime = datetime.datetime(2020, 3, 1)
    endTime = datetime.datetime(2020, 4, 1)
    ax = weatherPlot.createDataPlot('rain', startTime, endTime, PlotStep.WEEKLY, CalcType.SUM)
    plt.show()

    # Rain in month steps
    startTime = datetime.datetime(2020, 1, 1)
    endTime = datetime.datetime(2020, 10, 1)
    ax = weatherPlot.createDataPlot('rain', startTime, endTime, PlotStep.MONTHLY, CalcType.SUM)
    plt.show()

    # Max temperature for day - hour steps
    startTime = datetime.datetime(2020, 3, 1)
    endTime = datetime.datetime(2020, 3, 2)
    ax = weatherPlot.createDataPlot('outTemp', startTime, endTime, PlotStep.HOURLY, CalcType.MAX)
    plt.show()

    # Min temperature for year - month steps
    startTime = datetime.datetime(2019, 9, 1)
    endTime = datetime.datetime(2020, 9, 1)
    ax = weatherPlot.createDataPlot('outTemp', startTime, endTime, PlotStep.MONTHLY, CalcType.MIN)
    plt.show()

    # Total rainfall every year
    startTime = datetime.datetime(2015, 1, 1)
    endTime = datetime.datetime(2021, 1, 1)
    ax = weatherPlot.createDataPlot('rain', startTime, endTime, PlotStep.ANNUALLY, CalcType.SUM)
    plt.show()

    # Temperature plot    
    startTime = datetime.datetime(2019, 9, 1)
    endTime = datetime.datetime(2020, 9, 1)
    ax = weatherPlot.createTempPlot(startTime, endTime, PlotStep.MONTHLY)
    plt.show()
