import numpy as np
import pandas as pd
import pylab as pl
import csv
import glob
import os
from pyspark.sql import SQLContext
from pyspark.sql.types import *
import statistics as st

file_dir    = "LKQ/aug/dallas"
file_path   = os.path.join(".",file_dir)
files       = glob.glob(file_path + "/*")
files.sort()
cwd = os.getcwd()
filelds = ['PartNumber','QuantityAvailable','DateCreated']


def Sale(a):
    """
    Finds the total units sold in the period
    """
    sale = 0
    for i in range(len(a) -1 ):
        if a[i+1] < a[i]:
            sale += a[i] - a[i + 1 ]
    return sale

def Replenish(a):
    """
    Finds the total units replinished in the period
    """
    repl = 0
    for i in range(len(a) -1 ):
        if a[i+1] > a[i]:
            repl += a[i + 1] - a[i]
    return repl

def Analysis(a):
    sale , repl = Sale(a), Replenish(a)
    if (a[0] + repl ) != 0:
        percentage_sale = (float(sale) / (a[0] + repl )) *100 
    else: percentage_sale = 0

    return sale, repl, round(percentage_sale, 2)

first_flag = True
for file_no in range(0,7):
    
    #load csv in pandas and create dataframe
    f1 = pd.read_csv(files[ file_no ], sep="|", usecols=filelds)
    df = sqlContext.createDataFrame( f1 )
    
    #create (key,value) pair as (part_number, quantity_available, date_created)
    pair_df = df.rdd.map(lambda x: [x[0],[ [x[1]] , [x[2]] ]])

    #execute after first iteration
    if first_flag == False:
        #join pair_df with the old_df_acc
        df_acc = old_df_acc.join( pair_df )
        #flatten the values
        df_acc = df_acc.map(lambda (x, (a,b)):(x,(a+b)))

        old_df_acc = df_acc

    else:
        old_df_acc =  pair_df
        first_flag = False


res = df_acc.map(lambda (x, y): (x, Analysis(y))) \
.map(lambda (x,(a,b,c)): (x,[a]+[b]+[c]))

#res = df_acc.map(lambda (x, y): (x, round(st.stdev(y),2), Analysis(y))) \
#.map(lambda (x,y,(a,b,c)): (x,[y]+[a]+[b]+[c]))


#sorted by maximum sale
maximum_sold = res.sortBy(lambda (x,y): y[0] , ascending=False)

#write = maximum_sold.map(lambda (x,y): [x]+y)
#filter products with atleast one sale and map from (k,(v1,v2,v3)) to [k,v1,v2,v3] 
write = maximum_sold.filter(lambda (x,y): y[0]>=1).map(lambda (x,y): [x] +y)

#Convert RDD to DataFrame
df = sqlContext.createDataFrame(write, ['PartNumber', 'Sale','Replenish','PercentageSale'])

#save dataframe as csv
df.coalesce(1).write.format('com.databricks.spark.csv').options(header='true').save(cwd+'cv_out')

#all the procucts that have standard deviation of 1
stdOf1 = stdev.filter(lambda (x,y): y[0]>1.0)

stdev.filter(lambda (x,y): y>0.5).count()

#sale in range
t = res.filter(lambda (x,y): y[0]>10 and y[0] <50)



#ploting

d = maximum_sold.map(lambda (a,b): a)
#flattern the array [[a,b,c],[d]] to [a,b,c,d]
flattern = lambda a: [item for sublist in a for item in sublist]

def grp(pnos):
    for pno in pnos:
        a = df_acc.lookup(pno)
        a = flattern(a)
        pl.plot(list(range(len(a))),a)
    pl.show()

grp(d.take(10))

#generate x values depending on the length of Y
X = lambda a: np.arange(len(a))

#savitzky_golay window smooting
look = lambda a: np.array(flattern(df_acc.lookup(a)))

yhat = savitzky_golay(y, 21, 3) # window size 51, polynomial order 3

plt.plot(x,y)
plt.plot(x,yhat, color='red')
plt.show()


class Analysis:
    """Class for rate of change, ploting and other analysis
    Attributes: 
                values: list of inventory levels for the time period 
    """
    def __init__(self, pno):
        self.pno = pno
        self.values = self.look()

    flattern = lambda self,a: [item for sublist in a for item in sublist]
    generatex = lambda self,a: np.array(self.values)
    
    def look(self):
        """returns list of levels for the time period """
        return self.flattern( df_acc.lookup(self.pno) )

    def rateofchange(self,window=5):
        """Returns two array of the rate of change. (positive and negetive)"""
    
        y = self.values
        x = self.generatex(y)
        print(x)
        print(y)
    

a = Analysis('TO1038115')