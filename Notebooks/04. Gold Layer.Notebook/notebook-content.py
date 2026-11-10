# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "aba3ed44-d4fd-448a-9640-073ee0c35837",
# META       "default_lakehouse_name": "LH_Gold",
# META       "default_lakehouse_workspace_id": "e423af4f-88a7-47ac-a97a-eee54751b439",
# META       "known_lakehouses": [
# META         {
# META           "id": "aba3ed44-d4fd-448a-9640-073ee0c35837"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# #### 04. Gold Layer

# PARAMETERS CELL ********************

today_date= '9999-99-99' #'2026-08-13'
workspace= 'Na' #"fabric_DEV"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Loading silver table data

# CELL ********************

from pyspark.sql.functions import col

silver_table_path= f"abfss://{workspace}@onelake.dfs.fabric.microsoft.com/LH_Silver.Lakehouse/Tables/silver_data"
df= spark.read.format('delta').option('header', True).load(silver_table_path).filter(col('Processing_Date') == str(today_date))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Creating Dim_student table

# CELL ********************

from pyspark.sql.types import StructField,StructType, StringType, DoubleType, IntegerType, DecimalType
from delta.tables import DeltaTable

# Defining the column names and datatypes for the table

dim_student_schema= StructType(
    [
        StructField('Student_ID', StringType(), False),
        StructField('Name', StringType(), True),
        StructField('Age', IntegerType(), True),
        StructField('Gender', StringType(), True),
        StructField('Parent_Involvement', StringType(), True),
        StructField('Demographic_Group', StringType(), True),
        StructField('Internet_Access', StringType(), True),
        StructField('Learning_Disabilities', StringType(), True),
        StructField('Preferred_Learning_Style', StringType(), True),
        StructField('Language_Proficiency', StringType(), True)

    ]
)

# Creating the table in Deltatable method

DeltaTable.createIfNotExists(spark).tableName('Dim_student')\
            .addColumns(dim_student_schema)\
            .execute()


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### creating Dim_course table

# CELL ********************


dim_course_schema = StructType(
    [
    StructField('Course_ID', StringType(), False),
    StructField('Course_Name', StringType(), True),
    StructField('Grade_Level', StringType(), True)
    ]
)

DeltaTable.createIfNotExists(spark).tableName('Dim_course')\
            .addColumns(dim_course_schema)\
            .execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ##### Creating Fact table "fact_student_performance"

# CELL ********************

fact_performance_student_schema = StructType(
    [
    StructField('Student_ID', StringType(), False),
    StructField('Course_ID', StringType(), False),
    StructField('Enrollment_Date', StringType(), True),
    StructField('Completion_Date', StringType(), True),
    StructField('Status', StringType(), True),
    StructField('Final_Grade', StringType(), True),
    StructField('Attendance_Rate', DoubleType(), True),
    StructField('Time_Spent_on_Course_hrs', DoubleType(), True),
    StructField('Assignments_Completed', IntegerType(), True),
    StructField('Quizzes_Completed', IntegerType(), True),
    StructField('Forum_Posts', IntegerType(), True),
    StructField('Messages_Sent', IntegerType(), True),
    StructField('Quiz_Average_Score', DoubleType(), True),
    StructField('Assignment_Scores', StringType(), True),
    StructField('Assignment_Average_Score', DoubleType(), True),
    StructField('Project_Score', DoubleType(), True),
    StructField('Extra_Credit', DoubleType(), True),
    StructField('Overall_Performance', DoubleType(), True),
    StructField('Feedback_Score', DoubleType(), True),
    StructField('Participation_Rate', StringType(), True),
    StructField('Completion_Time_Days', IntegerType(), True),
    StructField('Performance_Score', DoubleType(), True),
    StructField('Course_Completion_Rate', StringType(), True)
    
    ]
)

DeltaTable.createIfNotExists(spark).tableName('fact_student_performance')\
.addColumns(fact_performance_student_schema).execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Loading Data Into Dim_student

# CELL ********************

# creating dataframe with selected columns for copying to dim_student table

df_selected_dim_student= df.select(
    'Student_ID',
    'Name',
    'Age',
    'Gender',
    'Parent_Involvement',
    'Demographic_Group',
    'Internet_Access',
    'Learning_Disabilities',
    'Preferred_Learning_Style',
    'Language_Proficiency'
)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ###### **one student can have multiple courses so in silver table same student id can be in multiple rows because same student doing different courses, the whole row ill not have duplicate rows cz we were filtering that. but same student id can make a multiple row with multiple courses on that table. so when we are creating dimension table we are removing duplicates again so same student id dont go to student dimension table.**

# CELL ********************

df_selected_dim_student_nodups= df_selected_dim_student.drop_duplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

dim_student_table= DeltaTable.forPath(spark, f'abfss://{workspace}@onelake.dfs.fabric.microsoft.com/LH_Gold.Lakehouse/Tables/dim_student')

dim_student_table.alias('target').merge(
    source=df_selected_dim_student_nodups.alias('source'),
    condition='target.Student_ID = source.Student_ID'
    ).whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Loading Data Into Dim_course

# CELL ********************

# creating dataframe with selected columns for dim_course table

df_selected_dim_course= df.select(
    'Course_ID',
    'Course_Name',
    'Grade_Level'
)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ###### **one student can take multiple courses. so in silver layer there is possibility same course id can occure to differenct students data. so when we are creating separate course table we have to remove duplicates to just keep only distinct value.**

# CELL ********************

df_selected_dim_course_nodups= df_selected_dim_course.drop_duplicates()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

dim_course_table= DeltaTable.forPath(spark, f'abfss://{workspace}@onelake.dfs.fabric.microsoft.com/LH_Gold.Lakehouse/Tables/dim_course')

dim_course_table.alias('target').merge(
    source=df_selected_dim_course_nodups.alias('source'),
    condition='target.Course_ID = source.Course_ID'
    ).whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### Loading Data Into fact_student_performance

# CELL ********************

df_selected_fact_student_performance= df.select(
    'Student_ID',
    'Course_ID',
    'Enrollment_Date' ,
    'Completion_Date' ,
    'Status' ,
    'Final_Grade' ,
    'Attendance_Rate',
    'Time_Spent_on_Course_hrs' ,
    'Assignments_Completed' ,
    'Quizzes_Completed' ,
    'Forum_Posts' ,
    'Messages_Sent' ,
    'Quiz_Average_Score' ,
    'Assignment_Scores' ,
    'Assignment_Average_Score' ,
    'Project_Score' ,
    'Extra_Credit' ,
    'Overall_Performance' ,
    'Feedback_Score' ,
    'Participation_Rate' ,
    'Completion_Time_Days',
    'Performance_Score' ,
    'Course_Completion_Rate',
    'processing_date'

)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

fact_student_performance= DeltaTable.forPath(spark, f'abfss://{workspace}@onelake.dfs.fabric.microsoft.com/LH_Gold.Lakehouse/Tables/fact_student_performance')

fact_student_performance.alias('target').merge(
    source= df_selected_fact_student_performance.alias('source'),
    condition = 'target.Student_ID = source.Student_ID AND target.Course_ID = source.Course_ID'
    
    ).whenMatchedUpdateAll() \
    .whenNotMatchedInsertAll() \
    .execute()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
