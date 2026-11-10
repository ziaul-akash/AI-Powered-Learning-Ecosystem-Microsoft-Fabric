# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# ### 01. RAW TO LANDING

# PARAMETERS CELL ********************

today_file='file' #'LMS_09-01-2023.csv'
processed_date= '9999-99-99' #'2026-08-08'
source_account= 'fabricdatalake685800'
source_container='lms-fabric-project'
srs_relative_path= 'raw'
destination_account='fabricdatalake685800'
destination_container='lms-fabric-project'


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### CREATING AZURE DATA LAKE STORAGE PATH

# CELL ********************



# Different methods of calling adls_path
# adls_path= 'abfss://%s@%s.dfs.core.windows.net/%s' % (container_name, storage_account_name, relative_path )
# adls_path= 'abfss://{}@{}.dfs.core.windows.net/{}'.format(container_name, storage_account_name, relative_path)

adls_path= f'abfss://{source_container}@{source_account}.dfs.core.windows.net/{srs_relative_path}'

print('abfss path' , adls_path)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import lit

latest_path= f"{adls_path}/{today_file}"
df = spark.read.format('csv').option('header', True).option('inferSchema', True).load(latest_path)

# checking if there is any data or atleast 1 row of data then it will process
if df.count() >= 1:
    print("The file has valid data")
    df= df.withColumn('processing_date', lit(processed_date))
    df.write.format('csv').option('header', True).partitionBy('processing_date').mode('append').save(f'abfss://{destination_container}@{destination_account}.dfs.core.windows.net/landing')
    print('Data has written to landing folder successfully')

else:
    print('This file contains only header row and no data')

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
