# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "da4ae510-7cdd-4fe1-bf55-208e7d61acb1",
# META       "default_lakehouse_name": "LH_Silver",
# META       "default_lakehouse_workspace_id": "e423af4f-88a7-47ac-a97a-eee54751b439",
# META       "known_lakehouses": [
# META         {
# META           "id": "da4ae510-7cdd-4fe1-bf55-208e7d61acb1"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# ### 03. Silver Transformations

# MARKDOWN ********************

# #### Data Cleaning

# PARAMETERS CELL ********************

### deciding which date's data will be cleaned and which workspace

today_date= '9999-99-99' #'2026-08-11'
workspace= 'NA' #"fabric_DEV"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

### Reading source data from bronze table 

from pyspark.sql.functions import col

fabric_bronze_path =  f"abfss://{workspace}@onelake.dfs.fabric.microsoft.com/LH_Bronze.Lakehouse/Tables/bronze_data"

df = spark.read.format('delta').option('header', True).load(fabric_bronze_path).filter(col('processing_date') == str(today_date))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### 01. Handling Duplicates

# CELL ********************

### Remove duplicates value if there is any

print('Count of rows before deleting duplicates: ', df.count())

df_nodups= df.dropDuplicates()

print('Count of rows after deleting duplicates: ', df.count())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### 02 - Handle missing or NULL values

# MARKDOWN ********************

# ##### 02. a . Drop rows with missing critical values

# CELL ********************

print('Rows before deleting critical null value rows : ' , df_nodups.count())

df_dropped = df_nodups.dropna(subset=['Student_ID','Course_ID' ,'Enrollment_Date'])

print('Rows after deleting critical null value rows : ' , df_dropped.count())


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### 02. b. Fill rows with default values

# CELL ********************

### setting the key value in key value pair in a dictionary 

df_filled = df_dropped.fillna(
    {
        "Name" : "Unknown",
        "Age": 0,
        "Gender": "Unknown",
        "Status": "In-progress",
        "Final_Grade": "N/A",
        "Attendance_Rate": 0.0,
        "Time_Spent_on_Course_hrs": 0.0,
        "Assignments_Completed": 0,
        "Quizzes_Completed": 0,
        "Forum_Posts": 0,
        "Messages_Sent": 0,
        "Quiz_Average_Score": 0.0,
        "Assignment_Average_Score": 0.0,
        "Project_Score": 0.0,
        "Extra_Credit": 0.0,
        "Overall_Performance": 0.0,
        "Feedback_Score": 0.0,
        "Parent_Involvement": "Unknown",
        "Demographic_Group": "Unknown",
        "Internet_Access": "Unknown",
        "Learning_Disabilities": "Unknown",
        "Preferred_Learning_Style": "Unknown",
        "Language_Proficiency": "Unknown",
        "Participation_Rate": "Unknown",
        "Completion_Time_Days": 0,
        "Performance_Score": 0.0,
        "Course_Completion_Rate": 0.0,
        "Completion_Date": '12/31/9999'

    }
)



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### 03. Standardize Date Formats

# CELL ********************

from pyspark.sql.functions import to_date , col

df_format = df_filled.withColumn('Enrollment_Date', to_date(col('Enrollment_Date'), 'M/d/yyyy'))\
                    .withColumn('Completion_Date', to_date(col('Completion_Date') , 'M/d/yyyy'))



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### 04. Check for Logical consistency


# MARKDOWN ********************

# ###### Completion_Date > Enrollment_Date

# CELL ********************

df_consistent = df_format.filter(col('Completion_Date') >= col('Enrollment_Date'))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Business Transformations

# MARKDOWN ********************

# #### 01. Completion_Time_Days 
# ##### Logic = Completion_Time_Days = Completion_Date - Enrollment_Date

# CELL ********************

#1 - We are subtracting CompletionDate - Enrollment_Date
#2 - We are converting that to integer

from pyspark.sql.functions import col

df_days = df_consistent.withColumn('Completion_Time_Days', (col('Completion_Date') - col('Enrollment_Date')).cast('int'))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### 02. Performance_Score
# ###### Logic : (Quiz_Average_Score * 0.2) + (Assignment_Average_Score * 0.2) + (Project_Score * 0.1)

# CELL ********************


df_score= df_days.withColumn('Performance_Score', (col('Quiz_Average_Score')*0.2 +col('Assignment_Average_Score')*0.2+col('Project_Score')*0.1).cast('decimal(10,2)'))


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### 03. Course_Completion_Rate
# 
# ##### Logic: IF(Completion_Time_Days <= 90, 'On Time', 'Delayed')

# CELL ********************

from pyspark.sql.functions import when,col

df_completion = df_score.withColumn('Course_Completion_Rate', when(col('Completion_Time_Days') <= 90, 'On-time').otherwise('Delayed'))

display(df_completion)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### SILVER TABLE CHECKING, IF NOT EXISTS THEN CREATE

# CELL ********************

# CHECK IF SILVER TABLE EXISTS OR CREATE SILVER TABLE

fabric_silver_path= f"abfss://{workspace}@onelake.dfs.fabric.microsoft.com/LH_Silver.Lakehouse/Tables/silver_data"

try:
    print('Reading data from Silver_data table: ')
    spark.read.format('delta').load(fabric_silver_path)
except:    
     
    print("No table found , Creating silver_data table: ")

    create_silver_table = f"""
    CREATE TABLE IF NOT EXISTS silver_data (
    Student_ID STRING,
    Name STRING,
    Age INTEGER NOT NULL,
    Gender STRING NOT NULL,
    Grade_Level STRING,
    Course_ID STRING,
    Course_Name STRING,
    Enrollment_Date DATE,
    Completion_Date DATE,
    Status STRING NOT NULL,
    Final_Grade STRING NOT NULL,
    Attendance_Rate DOUBLE NOT NULL,
    Time_Spent_on_Course_hrs DOUBLE NOT NULL,
    Assignments_Completed INTEGER NOT NULL,
    Quizzes_Completed INTEGER NOT NULL,
    Forum_Posts INTEGER NOT NULL,
    Messages_Sent INTEGER NOT NULL,
    Quiz_Average_Score DOUBLE NOT NULL,
    Assignment_Scores STRING,
    Assignment_Average_Score DOUBLE NOT NULL,
    Project_Score DOUBLE NOT NULL,
    Extra_Credit DOUBLE NOT NULL,
    Overall_Performance DOUBLE NOT NULL,
    Feedback_Score DOUBLE NOT NULL,
    Parent_Involvement STRING NOT NULL,
    Demographic_Group STRING NOT NULL,
    Internet_Access STRING NOT NULL,
    Learning_Disabilities STRING NOT NULL,
    Preferred_Learning_Style STRING NOT NULL,
    Language_Proficiency STRING NOT NULL,
    Participation_Rate STRING NOT NULL,
    Completion_Time_Days INTEGER,
    Performance_Score DOUBLE NOT NULL,
    Course_Completion_Rate STRING NOT NULL,
    Processing_Date DATE ); """

    spark.sql(create_silver_table)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### UPSERT TO SILVER TABLE FROM LATEST DATAFRAME (CLEANED AND TRANSOFRMED BRONZE DATA)

# CELL ********************

from delta.tables import DeltaTable

silver_table= DeltaTable.forName(spark, "LH_Silver.silver_data")


silver_table.alias('target').merge(
    source= df_completion.alias('source'),
    condition = "target.Student_ID = source.Student_ID AND target.Course_ID = source.Course_ID "
    )\
    .whenMatchedUpdateAll()\
    .whenNotMatchedInsertAll()\
    .execute()




# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# This coding below copied from claude.ai . 
# This is not a part of project. it is a specific way of checking
#  how many rows affected when we are using deltaTable method.

from pyspark.sql import Row

# Pull metrics from history
metrics = silver_table.history(1).select("operationMetrics").collect()[0]["operationMetrics"]

# Build a simple summary DataFrame, same shape as the SQL MERGE output
summary_df = spark.createDataFrame([
    Row(
        num_affected_rows=int(metrics.get("numTargetRowsUpdated", 0)) + int(metrics.get("numTargetRowsInserted", 0)) + int(metrics.get("numTargetRowsDeleted", 0)),
        num_updated_rows=int(metrics.get("numTargetRowsUpdated", 0)),
        num_deleted_rows=int(metrics.get("numTargetRowsDeleted", 0)),
        num_inserted_rows=int(metrics.get("numTargetRowsInserted", 0))
    )
])

summary_df.show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
