# import dependencies
import json
import pandas as pd
import numpy as np
import re
from sqlalchemy import create_engine
from sqlalchemy import update
import psycopg2
from config import db_password
import time

#ceate one function that runs under these conditions
def DataETL(wiki, kaggle, rating):
    file_dir = 'C:/Users/shaile/Desktop/movies_elt'
    with open(f'{file_dir}/{wiki}', mode='r') as file:
        wiki_movies_raw = json.load(file)
    kaggle_metadata = pd.read_csv(f'{file_dir}/{kaggle}', low_memory=False)
    ratings = pd.read_csv(f'{file_dir}/{rating}')
    #print(ratings)

    wiki_movies = [movie for movie in wiki_movies_raw
               if ('Director' in movie or 'Directed by' in movie)
                   and 'imdb_link' in movie
                   and 'No. of episodes' not in movie]
#create a non-destructive copy
    def clean_movie(movie):
        movie = dict(movie) 
        alt_titles = {} 
        for key in ['Also known as','Arabic','Cantonese','Chinese','French',
                    'Hangul','Hebrew','Hepburn','Japanese','Literally',
                    'Mandarin','McCune–Reischauer','Original title','Polish',
                    'Revised Romanization','Romanized','Russian',
                    'Simplified','Traditional','Yiddish']:
            if key in movie: 
                alt_titles[key] = movie[key]
                movie.pop(key) 
        if len(alt_titles) > 0:
            movie['alt_titles'] = alt_titles 


        # Merge all column names
        def change_column_name(old_name, new_name):
            if old_name in movie:
                movie[new_name] = movie.pop(old_name)
        change_column_name('Adaptation by', 'Writer(s)')
        change_column_name('Country of origin', 'Country')
        change_column_name('Directed by', 'Director')
        change_column_name('Distributed by', 'Distributor')
        change_column_name('Edited by', 'Editor(s)')
        change_column_name('Length', 'Running time')
        change_column_name('Original release', 'Release date')
        change_column_name('Music by', 'Composer(s)')
        change_column_name('Produced by', 'Producer(s)')
        change_column_name('Producer', 'Producer(s)')
        change_column_name('Productioncompanies ', 'Production company(s)')
        change_column_name('Productioncompany ', 'Production company(s)')
        change_column_name('Released', 'Release Date')
        change_column_name('Release Date', 'Release date')
        change_column_name('Screen story by', 'Writer(s)')
        change_column_name('Screenplay by', 'Writer(s)')
        change_column_name('Story by', 'Writer(s)')
        change_column_name('Theme music composer', 'Composer(s)')
        change_column_name('Written by', 'Writer(s)')
        return movie

    clean_movies = [clean_movie(movie) for movie in wiki_movies]
    wiki_movies_df = pd.DataFrame(clean_movies)
    
    try:
        wiki_movies_df['imdb_id'] = wiki_movies_df['imdb_link'].str.extract(r'(tt\d{7})')
        wiki_movies_df.drop_duplicates(subset='imdb_id', inplace=True)
        
    except:
        print("Error in imbd_link")
    #remove unwanted columns 
    wiki_columns_to_keep = [column for column in wiki_movies_df.columns if wiki_movies_df[column].isnull().sum() < len(wiki_movies_df) * 0.9]
    wiki_movies_df = wiki_movies_df[wiki_columns_to_keep]

    box_office = wiki_movies_df['Box office'].dropna()
    #convert data to string
    lambda x: type(x) != str
    box_office[box_office.map(lambda x: type(x) != str)]
    # Apply lambda method to box_office data
    box_office = box_office.apply(lambda x: ' '.join(x) if type(x) == list else x)

    form_one = r'\$\s*\d+\.?\d*\s*[mb]illi?on'
    form_two = r'\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)'

    box_office = box_office.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)
    # Extract and convert box office values
    box_office.str.extract(f'({form_one}|{form_two})')

    def parse_dollars(s):
        # Return NaN if not a string
        if type(s) != str:
            return np.nan
        # $###.# million
        if re.match(r'\$\s*\d+\.?\d*\s*milli?on', s, flags=re.IGNORECASE):
            s = re.sub('\$|\s|[a-zA-Z]','', s)
            value = float(s) * 10**6
            return value
        # $###.# billion
        elif re.match(r'\$\s*\d+\.?\d*\s*billi?on', s, flags=re.IGNORECASE):
            s = re.sub('\$|\s|[a-zA-Z]','', s)
            value = float(s) * 10**9
            return value
        elif re.match(r'\$\s*\d{1,3}(?:[,\.]\d{3})+(?!\s[mb]illion)', s, flags=re.IGNORECASE):
            s = re.sub('\$|,','', s)
            value = float(s)
            return value
        else:
            return np.nan

    #continue data cleaning 
    wiki_movies_df['box_office'] = box_office.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)
    budget = wiki_movies_df['Budget'].dropna()
    budget = budget.map(lambda x: ' '.join(x) if type(x) == list else x)
    budget = budget.str.replace(r'\$.*[-—–](?![a-z])', '$', regex=True)
    
    matches_form_one = budget.str.contains(form_one, flags=re.IGNORECASE)
    matches_form_two = budget.str.contains(form_two, flags=re.IGNORECASE)
    budget[~matches_form_one & ~matches_form_two]

    # Parse out the  data, and remove the numbers
    budget = budget.str.replace(r'\[\d+\]\s*', '')
    budget[~matches_form_one & ~matches_form_two]
    wiki_movies_df['budget'] = budget.str.extract(f'({form_one}|{form_two})', flags=re.IGNORECASE)[0].apply(parse_dollars)

    # Parse out the release date and drop all null values. 
    release_date = wiki_movies_df['Release date'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)
 
    date_form_one = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s[123]\d,\s\d{4}'
    date_form_two = r'\d{4}.[01]\d.[123]\d'
    date_form_three = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}'
    date_form_four = r'\d{4}'
   
    release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})', flags=re.IGNORECASE)
    #use the date and time 
    wiki_movies_df['release_date'] = pd.to_datetime(release_date.str.extract(f'({date_form_one}|{date_form_two}|{date_form_three}|{date_form_four})')[0], infer_datetime_format=True)

    running_time = wiki_movies_df['Running time'].dropna().apply(lambda x: ' '.join(x) if type(x) == list else x)

    #inspect data with expressions
    running_time.str.contains(r'^\d*\s*minutes$', flags=re.IGNORECASE).sum()
    running_time[running_time.str.contains(r'^\d*\s*minutes$', flags=re.IGNORECASE) != True]
    running_time.str.contains(r'^\d*\s*m', flags=re.IGNORECASE).sum()
    running_time[running_time.str.contains(r'^\d*\s*m', flags=re.IGNORECASE) != True]
    running_time_extract = running_time.str.extract(r'(\d+)\s*ho?u?r?s?\s*(\d*)|(\d+)\s*m')
    # Extract runnig_time values, and turn the values to numeric values
    running_time_extract = running_time_extract.apply(lambda col: pd.to_numeric(col, errors='coerce')).fillna(0)
    # Apply a fuction that will convert the data and save the output to the dataframe
    wiki_movies_df['running_time'] = running_time_extract.apply(lambda row: row[0]*60 + row[1] if row[2] == 0 else row[2], axis=1)

    # Drop the columns to not need.
    wiki_movies_df.drop('Box office', axis=1, inplace=True)
    wiki_movies_df.drop('Budget', axis=1, inplace=True)
    wiki_movies_df.drop('Running time', axis=1, inplace=True)

    # keep rows where the adult column is False, and then drop the adult column.
    kaggle_metadata = kaggle_metadata[kaggle_metadata['adult'] == 'False'].drop('adult',axis='columns')

    # Convert the datatype for video
    kaggle_metadata['video'] = kaggle_metadata['video'] == 'True'

    # Convert the datatype to numeric for budget, id and popularity datas
    kaggle_metadata['budget'] = kaggle_metadata['budget'].astype(int)
    kaggle_metadata['id'] = pd.to_numeric(kaggle_metadata['id'], errors='raise')
    kaggle_metadata['popularity'] = pd.to_numeric(kaggle_metadata['popularity'], errors='raise')
    kaggle_metadata['release_date'] = pd.to_datetime(kaggle_metadata['release_date'])

    # Datetime stampt, specify "unix"
    ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')
    movies_df = pd.merge(wiki_movies_df, kaggle_metadata, on='imdb_id', suffixes=['_wiki','_kaggle'])

    # Find out the index of the outlier row
    movies_df[(movies_df['release_date_wiki'] > '1996-01-01') & (movies_df['release_date_kaggle'] < '1965-01-01')].index
    movies_df = movies_df.drop(movies_df[(movies_df['release_date_wiki'] > '1996-01-01') & (movies_df['release_date_kaggle'] < '1965-01-01')].index)

    # Convert the language data to tuples
    movies_df['Language'].apply(lambda x: tuple(x) if type(x) == list else x).value_counts(dropna=False)
    
    movies_df.drop(columns=['title_wiki','release_date_wiki','Language','Production company(s)'], inplace=True)
    # make a function that fills in missing data for a column pair and then drops the redundant column.
    def fill_missing_kaggle_data(df, kaggle_column, wiki_column):
        df[kaggle_column] = df.apply(
            lambda row: row[wiki_column] if row[kaggle_column] == 0 else row[kaggle_column]
            , axis=1)
        df.drop(columns=wiki_column, inplace=True)

    # run the function for the three column pairs to fill in zeros.
    fill_missing_kaggle_data(movies_df, 'runtime', 'running_time')
    fill_missing_kaggle_data(movies_df, 'budget_kaggle', 'budget_wiki')
    fill_missing_kaggle_data(movies_df, 'revenue', 'box_office')

    # Check the dataframe columns
    for col in movies_df.columns:
        lists_to_tuples = lambda x: tuple(x) if type(x) == list else x
        value_counts = movies_df[col].apply(lists_to_tuples).value_counts(dropna=False)
        num_values = len(value_counts)
        #if num_values == 1:
            #print(col)

    # Drop the video column
    movies_df['video'].value_counts(dropna=False)

    # Rearange the columns
    movies_df = movies_df[['imdb_id','id','title_kaggle','original_title','tagline','belongs_to_collection','url','imdb_link',
                        'runtime','budget_kaggle','revenue','release_date_kaggle','popularity','vote_average','vote_count',
                        'genres','original_language','overview','spoken_languages','Country',
                        'production_companies','production_countries','Distributor',
                        'Producer(s)','Director','Starring','Cinematography','Editor(s)','Writer(s)','Composer(s)','Based on'
                        ]]

    # Rename the columns
    movies_df.rename({'id':'kaggle_id',
                    'title_kaggle':'title',
                    'url':'wikipedia_url',
                    'budget_kaggle':'budget',
                    'release_date_kaggle':'release_date',
                    'Country':'country',
                    'Distributor':'distributor',
                    'Producer(s)':'producers',
                    'Director':'director',
                    'Starring':'starring',
                    'Cinematography':'cinematography',
                    'Editor(s)':'editors',
                    'Writer(s)':'writers',
                    'Composer(s)':'composers',
                    'Based on':'based_on'
                    }, axis='columns', inplace=True)

    # count for each movie (movieID) and ratings (user ID)
    rating_counts = ratings.groupby(['movieId','rating'], as_index=False).count()                 .rename({'userId':'count'}, axis=1)                 .pivot(index='movieId',columns='rating', values='count')
    rating_counts.columns = ['rating_' + str(col) for col in rating_counts.columns]
    movies_with_ratings_df = pd.merge(movies_df, rating_counts, left_on='kaggle_id', right_index=True, how='left')
    movies_with_ratings_df[rating_counts.columns] = movies_with_ratings_df[rating_counts.columns].fillna(0)

    # Connect with PostgreSQL
    "postgres://[user]:[password]@[location]:[port]/[database]"
    db_string = f"postgres://postgres:{db_password}@127.0.0.1:5432/movie_data"
    engine = create_engine(db_string)
    movies_df.to_sql(name='movies', con=engine, if_exists='replace', index=False)
    
    rows_imported = 0
    #get the start_time from time.time()
    start_time = time.time()
    for data in pd.read_csv(f'{file_dir}/ratings.csv', chunksize=1000000):
        print(f'importing rows {rows_imported} to {rows_imported + len(data)}...', end='')
        data.to_sql(name='ratings', con=engine, if_exists='append')
        rows_imported += len(data)

        # add elapsed time to final print out
        print(f'Done. {time.time() - start_time} total seconds elapsed')

    print("It is working")


DataETL("wikipedia.movies.json", "movies_metadata.csv", "ratings.csv")


