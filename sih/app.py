#you can import library
from flask import Flask,render_template,request
from googletrans import Translator
import pickle
import pandas as pd
from rapidfuzz import fuzz
import spacy
# from flask_sqlalchemy import SQLAlchemy
from spellchecker import SpellChecker
import httpcore
#connection for the database
import mysql.connector

app = Flask(__name__)


#connection with the database
connection = mysql.connector.connect(
    host='localhost', username='root', password='cu3681', database='testing'
)
# app.config['SQLAlCHEMY_DATABASE_URI']='sqlite:///db.sqlite3'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

# db=SQLAlchemy(app)

translator = Translator()
#nlp model loading
nlp = spacy.load("en_core_web_trf")
#loading of dataset
countries = pd.read_csv(r"final.csv")       #database change from csv to sql

# countries["category"] = "country"
countries["name"] = countries["name"].apply(lambda x: x.lower())

# done till above

ld_list1 = list((countries["name"]))

def fuzzy_match_location(user_input, threshold=75.5):
    user_input = user_input.lower()
    matches = []
    for location in ld_list1:
        ratio = fuzz.token_set_ratio(user_input, location)
        if ratio >= threshold and abs(len(location) - len(user_input)) <= 2:
            matches.append((location, ratio, countries[countries["name"] == location]["category"].iloc[0]))

    matches = sorted(matches, key=lambda x: x[1], reverse=True)

    if matches:
        return matches[0]
    else:
        return None
def correct_names(text):
    spell = SpellChecker()
    misspelled = spell.unknown(text.split())
    misspelled_list = list(misspelled)
    cleaned_list = [element[1:] if element[0] == ',' else element[:-1] if element[-1] == ',' else element for element in misspelled_list]
    doc = nlp(text)
    text = text.title()
    lst = []
    for word in doc.ents:
     lst.append((word.text))
    l_list = [element.lower() for element in lst]
    set1 = set(l_list)
    set2 = set(cleaned_list)
    unique1 = set1 - set2
    unique2 = set2 - set1
    common = set1 & set2
    result = unique1.union(unique2).union(common)
    result_list = list(result)
    results = [fuzzy_match_location(location) for location in result_list]
    first_index = []
    for element in results:
     if element is not None:
      first_index.append(element[0])
     my_list = []
    for item in first_index:
     row = countries[countries["name"] == item].iloc[0]
     latitude = row["latitude"]
     longitude = row["longitude"]
     category = row["category"]
     my_list.append(f"{item} , {category} ,{latitude},{longitude}")
    return my_list




def translate_text(text, dest='en'):
    if translator.detect(text)=='en':
        return text
    else :
        result = translator.translate(text, dest=dest)
        return result.text
def check_and_return_list(data_list):
    if not data_list:
        return "This is not present in the database"
    else:
        return data_list   

#database functions
    
def history_request(data):
    # Example values to be inserted into the table
    values = (data,)  # Add a comma to create a tuple with a single element

    # Create a cursor
    cursor = connection.cursor()

    # SQL query to insert values into the table
    insert_query = "INSERT INTO history ( previous_details) VALUES (%s)"

    # Execute the query with the provided values
    cursor.execute(insert_query, values)

    # Commit the changes to the database
    connection.commit()

    # Close the cursor and connection

#end of database_rquest_for_history
    
def history_response():
    cursor = connection.cursor()

    query = "select previous_details FROM history ORDER BY ID DESC LIMIT 5;"

    # Executing the query
    cursor.execute(query)


    # Fetching the result
    result = cursor.fetchall()
    
    connection.commit()
    print(result)
    # Close the cursor and connection
    # cursor.close()
    # connection.close()
    
    return result



    
@app.route("/",methods=['GET','POST'])
def hello_world():
    request_type_str=request.method
    if request_type_str == 'GET':
        output=""
        return render_template('index.html',output=output)
    else:
        
        test=request.form['text']
        history_request(test)
        text = translate_text(test)
        check=correct_names(text)
        final=check_and_return_list(check)
    
        yet=history_response()
        list_of_tuples=yet
        list_of_strings=[tpl[0] for tpl in list_of_tuples]
        print(final)
        return render_template('index.html',output=final,history=list_of_strings)