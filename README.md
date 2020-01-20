# movies_etl

# module 

In this module, we learned how to use the Extract, Transform, Load (ETL) process to create data pipelines. We are able to do the following: 
- Create an ETL pipeline from raw data to a SQL database.
- Extract data from disparate sources using Python.
- Clean and transform data using Pandas.
- Use regular expressions to parse data and to transform text into numbers.
- Load data with PostgreSQL.

Using the three files (ratings, movie_metadata, wiki JSON), we were able to see a lot of information about movies, including budgets and box office returns, cast and crew, production and distribution, and so much more. Using juypter note book, we were able to transform and clean the data. From there, the data was imported the cleaned movies and ratings data to Postgres SQL. 

# Challenge

In this challenge, we wrote a Python script that performs all three ETL steps on the Wikipedia and Kaggle data. We left out any code that performs exploratory data analysis, and you may added a code to handle potentially unforeseen errors due to changes in the underlying data. We begin by reading the function that takes the three arguments, which included Wiki, Kaggle, and movie data. Then we used the functions from the Jupyter Notebook to the function and removed the existing data from the sql file. To ensure the sucess of this, we ran the function to ensure the function was running properly.Lastly, we used the try-except blocks to account for any problems and issues that may rise with the data. 

For this analysis, we made the following assumptions as we were cleaning the data and duing this challenge. 

- We used the try except for the imdb_id to ensure the parameters were with in 7 digits. This excluded all data that did not include ids that were more than seven and less than seven. This imdb is was used tSince we’re going to merge merge with the Kaggle data, we want to make sure that ate data. 

- We dropped columns that were 90% empty due to data qaulity issues. We assumed that the data in the colums was incomplete and it was best to leave it off and work with the complete dataset you have avalible.

- In our analysis, we assumed thet the data sturcture of the files was the same. We merged the data columns and we are assuming that all  files have a one to one relationship. There was a need to consolidate columns with the same data into one column. 

- We dropped the null values to better help us with our analytics. For example, we removed the null values of the release date to ensure that we retrive the most up to date data.  

- We trimmed down the columns since some of the columns have data stored as text when it should be a different data type, such as numeric data or datetimes. We assiumed that this would help us better understand the questkons. 



