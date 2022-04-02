###############################################################################
## 📚 Importing all the libraries and dependencies that the app needs to use ##
###############################################################################

# Creating the interface and accessing data 
import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
import time
import SessionState  #SessionState is an important libray that allows the button to stay "activated" after users 
                     #click on other components in the app. This is a library that is sepcific to streamlit. Find the library in the same github repo.

import logging
import json


# Basic data processing 
import random
import pandas as pd 
import numpy as np
from string import ascii_uppercase, digits

# Data analysis 
from bertopic import BERTopic
from hdbscan import HDBSCAN


# Authenticate to Firestore with the JSON account key.
# This steps connect that database to the interface
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="automatic-affinity-mapping")

###############################################################################
### 👋 Interface Begins Here ##################################################
###############################################################################

# Write the title of the app. strings within the quotation marks function like markdown. 
st.write("# findPattern.")

# Create a room number composed of 9 characters (english letters and numbers)
def room_number_generator():
    str0= random.sample(ascii_uppercase,4)+random.sample(digits,4)+random.sample(ascii_uppercase,1)
    return ''.join(str0)

# Allow users to select who they are and correpond their role to respective interface
user_mode = st.selectbox('Who are you?', ['-','Facilitator (Create New Room)','Facilitator (Go to Existing Room)','Participant'])

##################################
### State 1: Introduction Page ###
##################################


# When the role is not selected, the introduction page is displayed
# In the introduction page gives users an overview on what the app does and what technology it uses
if user_mode == '-':

    # Section 1: Overview
    st.write('## 👋 Welcome to findPattern.')
    st.write('findPattern helps you brainstorm and find common themes in the ideas FASTER.') 
    st.image("quickshow.gif")
    st.write('findPattern uses state-of-the-art Natural Language Processing technique--BERT to understand and process a huge number of texts faster than a human brain could do.')
    
    # Section 2: How does the app work?
    st.write("## 👉 How does the app work?")
    with st.expander("How does the app work?"):
        st.image('./Images/How it Works.png')

    # Section 3: What technology does this app use?
    st.write("## 👉 What technology does this app use?")
    with st.expander("What technology does this app use?"):

        st.write('This app uses a type of algorthm called Topic modeling. Topic modeling is the machine learning jargon for finding topics within text without telling the machine what kind of topics there might be. Specifically, this app uses a Python library called BERTopic, which is created by Maarten Grootendorst. BERTopic combines a handful of useful existing python libraries, inlcuding a text encoder (SentenceTransformer), a dimension reduction tool (UMAP), and a clustering tool (HDBSCAN). So what are these python libraries doing and why does combining them help us do topic modeling? ')
        st.write('### Encoder -- SentenceTransformer')
        st.write('A text encoder reads the text input, considers the context and meaning of words in the text input, and represents text input in probability, which we call word embeddings. An example of the word embeddings is below. Each word is represented as a vector of 50 values in the GloVe model. Each of the values indicates a property of the word.')
        st.image('https://github.com/cyrushhc/findPattern/blob/main/Encoding%20exmaple.png?raw=true')
        st.write('[Image Source: Jay Alammar](https://jalammar.github.io/illustrated-word2vec/)')
        st.write('This is where the powerful BERT comes in: BERT is a empirically powerful encoder that produces state of the art results (Devlin et al., 2019; Thompson & Mimno, 2020). The SentenceTransformers library in Python uses BERT as encoder (Reimers & Gurevych, 2019). BERT can be extended to achieve several tasks to understand and process natural language. One such example is BERTopic.')
        st.write('### Reduce Dimension -- UMAP')
        st.write('As mentioned before, after encoding each response (it could be a document, a sentence, or a word), each response will be represented in a list of numbers. To be exact, for SentenceTransformer encoder, each response would be represented with a list of 768 numbers. And this is a large number of dimensions for the computer to process! Large dimensions requires more time and computational resource to process. Moreover, not every dimension would be useful in separating responses into clusters. For example, if we have four words, [cats, dogs, girls, boys] and that one of the dimension is whether the text is a living object, then all four text would be very similar in that respect––making that dimension less useful. This is why we reduce dimension with UMAP. UMAP is also an powerful dimension-reduction techqniques that preserve the high dimensional structure very well after reducing dimensions. After the reduction, the list of 768 values becomes a list of 5 values. This is so that you do not have to wait forever for the results to show!')
        st.write('### Clustering - HDBSCAN')
        st.write('The last step of the BERTopic library is the clustering step. BERTopic uses HDBSCAN, which is a model that identifies clusters by the density of the data points, which is similar to the way human eyes identify clusters. Here is a great video telling you how HDBSCAN clusters datapoints.')
        st.image('HDBSCAN.gif')

###########################################################
### State 2: Faciliator who wants to create a new room ###
###########################################################

elif user_mode == "Facilitator (Create New Room)":
    
    # Reminder
    with st.expander("Reminder for before you start"):
        st.write("1. Currently, findPattern only supports finding clusters among a larger number of responses (>50). We will work hard to resolve the data size constraints and hope to support users dealing with a fewer responses")
        st.write("2. For the model to work, please remind the participants to provide one idea per response box. For example, if the prompt is 'what do you want to eat for breakfast', the responses 'milk and bread' should be separated into 'milk' and 'bread' in separate response box.")



    st.write("## ✋ Discussion Prompt")
    
    # Create the interface to allow facilitators to input the questions they want to ask participants
    prompt_name = st.text_input('Prompt')
    prompt_description = st.text_input('What kind of response do you want participants to give? (e.g. each response should be 1-2 sentence.)')

    # Allow facilitators to choose how many responses they want to get from participants
    number_of_response = st.slider(label ='Number of responses for each participant', min_value = 0, max_value = 20, value = 5)

    # Alloq facilitators to decide whether tbey want to let participants see others' responses, defaulted to false
    cross_pollination = st.checkbox("Let participants see other participants' responses", False) 

    # Create the create_room button and let the session remembers its state
    create_room = st.button("Create a Room")
    ss = SessionState.get(create_room = False)
    room_number = st.empty()
    ss_r = SessionState.get(room_number = None)

    # Add a variable to keep track of whether it's the first time the create_room button is creeated
    initial_state = st.empty()
    ss_init = SessionState.get(initial_state = None)

    # when the create_room button is clicked, it would be activated (True). Due to streamlit's design choice, 
    # the button state is not memorized in the session (browser tab). To memorize that in the session, 
    # We need to use the session_state variable.
    if create_room:
        ss.create_room = True
        # The room number is only generated once, so that we will tie it to the button instead of the state of the button
        # If we tie it to the state of the button (which should be true throughout the app), then the room number would keep changing
        ss_r.room_number = room_number_generator()
        ss_init.initial_state = 0

    # Using the try catch syntax to avoid displaying the error caused by non existing variables. 
    try : 
        # This is actually what happens when the button is clicked
        if ss.create_room:
            st.write("")
            st.write("\n")
            st.write(f"## 🔗 Room Number: {ss_r.room_number}")
            
            # Allow facilitator to share the room info
            st.write("**Copy-paste and share** this invite info with your participants")
            st.code(f"👉 Join here https://share.streamlit.io/cyrushhc/findpattern/main/myapp.py\n🚪 Room number: {ss_r.room_number}")
            
            # Connecting the app the the database based on the room number
            doc_ref = db.collection("Room").document(f"Room {ss_r.room_number}")
            if ss_init.initial_state == 0:

                # Create a new entry in the database that contains the information about this room.
                doc_ref.set({
                    "prompt_question": prompt_name, # Tracks the name of the prompt
                    "prompt_description":prompt_description, # Tracks the prompt description
                    "responses": [], # Tracks participants responses. Each entry will contain the responses of one participant 
                    "room_number": ss_r.room_number,# Tracks the room number
                    "num_response":number_of_response,  # This tracks the number of responses allowed for users
                    "collect_response": True, # This tracks whether participants can still submit responses
                    "ready_to_cluster": False, # This tracks whether to show the clustering section of the app
                    'clustering_results': [], # This tracks the results of the clustering model. each entry will be one cluster of data
                    "no_cluster": False, # This is used to check whether the cluster results contains data that doesn't belong to any clusters
                    "cross_pollination": cross_pollination, # This tracks whether participants can see each others' responses
                })
                ss_init.initial_state += 1
            
            # Shows the facilitators an example what the users would see on the interface
            with st.expander("View Participant Interface"):
                st.image("Example-participants.png")
    except: 
        st.write('')
        
    

    try:
        # Let facilitators see the responses of the participnats
        print(ss_r.room_number)
        st.write("## 📝 Participant Response")
        doc = doc_ref.get().to_dict()  

        # Create a button for viewing participants responses
        # Since the real-time update function is not well supported for Python on Firebase,
        # I worked around this by allowing users to see update everytime they click the button
        view_responses = st.button("View Participants' Responses")
        st.write("Not all participants might have submitted their responses. Click the button periodically to see more responses streaming in.")
        ss2 = SessionState.get(view_responses = False) 
        
        if view_responses:
            ss2.view_responses = True

        if ss2.view_responses == True:
            # If there is no responses yet, show the status.
            if doc['responses'] == []:
                st.write("No response submitted yet")
            else:
                st.table(doc['responses'])
        
        # button the close paritipants ability to submit new responeses

        end_collection = st.button("Close Participant Response")
        ss3 = SessionState.get(end_collection = False) 

        if end_collection:
            ss3.end_collection = True

        if ss3.end_collection == True:
            # When the button is clicked, the next sections will be activated because "read_to_cluster" is set to True.
            doc_ref.update({
                "collect_response": False,
                "ready_to_cluster": True,
            }
            )
    except:
        st.write("")    

    try:    
        doc_ref = db.collection("Room").document(f"Room {ss_r.room_number}") 
        
        # Get the data stored in the room
        doc = doc_ref.get().to_dict()
        if  doc['ready_to_cluster'] == True:
            st.write('## 🧩 Find Patterns')

            # Inform the users different settings that the app affords
            with st.expander("How to choose a setting"):
                st.write("I would reommend going with `generic` first. If you find that the results are too generic, then choose `nuanced`.")
                st.write("When you choose `generic`, the model is going to lump together smaller clusters that are simliar.")
                st.write("When you choose `nuanced`, the model would show you the smaller clusters before they are lumped together.")

            # Let users choose the types of model results they want to get
            result_fidelity = st.radio("Do you want more a more nuanced results or a more high-level generic clustering resutls?", ['Nuanced', 'Generic'])
            find_pattern = st.button("Find Pattern")
            ss4 = SessionState.get(find_pattern = False) 

            if find_pattern:
                ss4.find_pattern = True
                
            if ss4.find_pattern == True:
                
                # When the find_pattern button is clicked, start the data analysis 
                with st.spinner('Finding patterns in your data...'):

                    # If users choose to get more "Nuanced" results, 
                    if result_fidelity == 'Nuanced':
                        # Set the clustering model (HDBSCAN) to retain the lower-level clusters (before they are consolidated into bigger clusters)
                        clustering_model = HDBSCAN(metric='euclidean', cluster_selection_method='leaf', prediction_data=True)

                        # Load the bertopic model, set the clustering model to the one created above
                        model = BERTopic(hdbscan_model = clustering_model, calculate_probabilities= True)   
                    

                    else: 
                        # Otherwise, use the default clustering model embeded in bertopic
                        model = BERTopic(calculate_probabilities= True)  

                    # Process the data stored in the database so that the bertopic model can handle the structure
                    new_list = []
                    for i in doc['responses']: 
                        new_list+=(list(i.values()))                    
                    
                    # Remove the empty strings in the data (which happens when a participant doesn't end up using all the responses)
                    new_list = [x for x in new_list if x]

                    # Start finding pattern in the data using the model 
                    try:
                        pred, prob = model.fit_transform(new_list)
                        # Manually lower the threshold of probabilty assignment so that more documents could be asgined to clusters
                        threshold = 0.3
                        for document in np.where(np.array(pred) == -1)[0]:
                            if max(prob[document]) >= threshold:
                                pred[document] = int(np.where(prob[document] == max(prob[document]))[0])
                        
                        # Animation for surprises and shows the state of the app.
                        st.success('Here you go! 🤟')
                        st.balloons()

                    # If it doesnt't work, show users what the potential problem might be 
                    except:
                        st.write('The model could not find clusters. This could be because the datasize is too small or because there is only one topic')

                    



                clustering_results = [] # Record the clustering results to store it into the database
                downloadable_results = pd.DataFrame() # Record the clustering results to allow donwloading. Firebase have a particular format that it takes, so I created another variable to save the data for downloading
                blank_rows = pd.DataFrame([['', ''],['', ''],['Next Cluster Starts','']]) # This is created to separate the clusters in the CSV file for better viewing
                st.write('## The patterns in your data.\n')

                # Instruction for users to interpret the results
                with st.expander("Interpret the results"):
                    st.write('''The model has found some pattern in your data.
                            Each cluster contains participants responses that the model considers to be similar
                            The **Probability** column shows you how probable does that response belong to the assigned cluster.
                            For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                            ''')
                    st.image("Example - Interpretation.png")


                # Identify the number of clusters to display. Distinguished by whether there are data that doesn't have a cluster (-1)
                if -1 in pred:
                    num_cluster = len(model.get_topic_info())-1
                else: 
                    num_cluster = len(model.get_topic_info())


                # Display each clusters            
                for i in range(num_cluster):                
                    st.write(f'### Cluster {i+1}')
                    
                    # Find the index of the documents that belong to the cluster 
                    topic_index = np.where(np.array(pred) == i)
                    
                    # Store the documents in an array
                    a_cluster = np.array(new_list)[topic_index]

                    # Store the probability vector (to belong in different cluster) of each document into another array
                    document_prob = np.array(prob)[topic_index]

                    
                    
                    if type(document_prob[0]) == float or type(document_prob[0]) == int :
                        max_doc_prob = document_prob

                    # If there are more than one cluster, then take the max value out of the probability vector. 
                    # This value would be the probability for that document to belong to the cluster it is assigned to
                    else:
                        max_doc_prob = document_prob.max(axis=1)
                    
                    # Store the documents and the probability into the dataframe for display 
                    df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                    df = df.sort_values('Probability', ascending= False)
                    
                    # Store the documents and the probability into the dataframe for downloading
                    downloadable_results = downloadable_results.append(blank_rows) 
                    downloadable_results =downloadable_results.append(df)


                    # Display the most relevant document.
                    st.table(df.head())
                    
                    # Allow users to see the rest of the responses in the cluster if they want to 
                    with st.expander("View All Responses in this Cluster"):
                        st.table(df.iloc[5:])

                    
                    # Converting the dataframe into a form that is storable on firebase
                    lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                    lst_storage = lst_storage.tolist()
                    dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                    cluster_dict = dict(zip(dictionary_keys, lst_storage))
                    clustering_results.append(cluster_dict)

                
                # Displaying the documents that don't have a cluster 
                if -1 in pred:
                    st.write("### Here are the responses that the model couldn't find a cluster for")
                    
                    # Find the index of the documents that doesn't have a cluster 
                    topic_index = np.where(np.array(pred) == -1)

                    # Store the documents in an array
                    a_cluster = np.array(new_list)[topic_index]

                    # Store the probability vector (to belong in different cluster) of each document into another array
                    document_prob = np.array(prob)[topic_index]

                    if type(document_prob[0]) == float or type(document_prob[0]) == int :
                        max_doc_prob = document_prob

                    # If there are more than one cluster, then take the max value out of the probability vector. 
                    # This value would be the probability for that document to belong to the cluster it is assigned to
                    else:
                        max_doc_prob = document_prob.max(axis=1)

                    # Store the documents and the probability into the dataframe for display 
                    df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                    df = df.sort_values('Probability', ascending= False)

                    # Store the documents and the probability into the dataframe for downloading
                    blank_rows_2 = pd.DataFrame([['', ''],['', ''],['Responses with No Cluster','']])
                    downloadable_results = downloadable_results.append(blank_rows) 
                    downloadable_results =downloadable_results.append(df)
                    st.table(df)

                    # Converting the dataframe into a form that is storable on firebase
                    lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                    lst_storage = lst_storage.tolist()
                    dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                    cluster_dict = dict(zip(dictionary_keys, lst_storage))
                    clustering_results.append(cluster_dict)

                    # Tell the system that this room has data that doesn't have a cluster
                    # So that when it is being called by the participants, the system would dael accordingly
                    doc_ref.update({
                        "no_cluster":  True,
                    })
                
                # Store the clustering results into the database
                try:
                    # remove the existing results first
                    doc_ref.update({
                        "clustering_results":  [],
                    })

                    # Store the updated results
                    doc_ref.update({
                        "clustering_results":  clustering_results,
                    })
                except:
                    st.write('Cannot write the results')
                
                # Allow downloading the clustering in CSV files
                csv = downloadable_results.to_csv().encode('utf-8')
                st.download_button("Download your clustering data",  csv, 'Cluster Results from findPattern.csv')

    except:
        st.write('')
    
###########################################################
### State 3: Faciliator who wants to access a new room ###
###########################################################

elif user_mode == 'Facilitator (Go to Existing Room)':
    try:
        # Create the room_number input 
        room_number = st.text_input('Room Number', value = 0)
    except:
        pass
    
    try:
        # Connect with the database and get the data based on the room number 
        doc_ref = db.collection("Room").document(f"Room {room_number}")
        doc = doc_ref.get()
        doc = doc.to_dict()
        prompt_name = doc['prompt_question'] 
        prompt_description = doc['prompt_description']

        # Display room information
        st.write(f"### 🙃 Prompt: {prompt_name}")
        st.write(prompt_description)

        # Allow different actions
        goal = st.radio('What do you want to do?',['See existing results', 'Create new cluster results'])
        
        if goal == "See existing results":
            if doc['clustering_results'] == []:
                st.write('There is no results yet. Create new cluster results instead')
            else:

                # Instruction for users to interpret the results
                with st.expander("Interpret the results"):
                    st.write('''The model has found some pattern in your data.
                        Each cluster contains participants responses that the model considers to be similar
                        The **Probability** column shows you how probable does that response belong to the assigned cluster.
                        For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                        ''')
                    st.image("Example - Interpretation.png")
                st.write('## The patterns in the ideas\n')

                downloadable_results = pd.DataFrame() # Record the clustering results to allow donwloading. Firebase have a particular format that it takes, so I created another variable to save the data for downloading
                blank_rows = pd.DataFrame([['', ''],['', ''],['Next Cluster Starts','']]) # This is created to separate the clusters in the CSV file for better viewing
                

                # Display each clusters            
                for c_id in range(len(doc['clustering_results'])):
                    
                    # For the 0 to n-1 clusters, they will definitely be meaningful clusters
                    if c_id <len(doc['clustering_results'])-1:
                        st.write(f'### Cluster {c_id+1}')
                    
                    # For the last cluster, depending on the types of room, 
                    else:
                        # room that do have a data that don't have a cluster
                        if doc['no_cluster'] == True: 
                            st.write("### Here are the responses that the model couldn't find a cluster for")
                        
                        # room that don't have a data that don't have a cluster
                        else: 
                            st.write(f'### Cluster {c_id+1}')
                    
                    # Take the data from the database and process them in a way that is displayable on streamlit
                    display = np.array(list(dict.values(doc['clustering_results'][c_id])))
                    display = pd.DataFrame(display, columns = ['Response', 'Probability'])
                    display = display.sort_values('Probability', ascending= False)
                    
                    # Store the documents and the probability into the dataframe for downloading
                    downloadable_results = downloadable_results.append(blank_rows)
                    downloadable_results = downloadable_results.append(display)

                    # Display the most relevant document.
                    st.table(display.head()) 

                    # Allow users to see the rest of the responses in the cluster if they want to 
                    with st.expander ("View More Responses in this Cluster"):
                        st.table(display)
                    
                csv = downloadable_results.to_csv().encode('utf-8')
                st.download_button("Download your clustering data",  csv, 'Cluster Results from findPattern.csv')

        
        # If the users want to create new cluster results, repeat the steps from 
        else: 
            
            # Let facilitators see the responses of the participnats
            st.write("## 📝 Participant Response")

            # Create a button for viewing participants responses
            # Since the real-time update function is not well supported for Python on Firebase,
            # I worked around this by allowing users to see update everytime they click the button
            view_responses = st.button("View Participants' Responses")
            ss2 = SessionState.get(view_responses = False) 
            

            if view_responses:
                ss2.view_responses = True
            
            try: 
                if ss2.view_responses == True:
                    # If there is no responses yet, show the status.
                    if doc['responses'] == []:
                        st.write("No response submitted yet")

                    # Otherwise, show the responses
                    else:
                        st.table(doc['responses'])
            except:
                pass
            
            # button the close paritipants ability to submit new responeses
            end_collection = st.button("Close Participant Response")
            ss3 = SessionState.get(end_collection = False) 

            if end_collection:
                ss3.end_collection = True

            try: 
                if ss3.end_collection == True:
                    # When the button is clicked, the next sections will be activated because "read_to_cluster" is set to True.
                    doc_ref.update({
                        "collect_response": False,
                        "ready_to_cluster": True,
                    }
                    )
            except:
                pass
            
            try:    
                if doc['ready_to_cluster'] == True:
                    st.write('## 🧩 Find Patterns')

                    # Inform the users different settings that the app affords
                    with st.expander("How to choose a setting"):
                        st.write("I would reommend going with `generic` first. If you find that the results are too generic, then choose `nuanced`.")
                        st.write("When you choose `generic`, the model is going to lump together smaller clusters that are simliar.")
                        st.write("When you choose `nuanced`, the model would show you the smaller clusters before they are lumped together.")

                    # Let users choose the types of model results they want to get
                    result_fidelity = st.radio("Do you want more a more nuanced results or a more high-level generic clustering resutls?", ['Nuanced', 'Generic'])
                    find_pattern = st.button("Find Pattern")
                    ss4 = SessionState.get(find_pattern = False) 

                    if find_pattern:
                        ss4.find_pattern = True

                    if ss4.find_pattern == True:

                        # When the find_pattern button is clicked, start the data analysis 
                        with st.spinner('Finding patterns in your data...'):

                             # If users choose to get more "Nuanced" results, 
                            if result_fidelity == 'Nuanced':
                                # Set the clustering model (HDBSCAN) to retain the lower-level clusters (before they are consolidated into bigger clusters)
                                clustering_model = HDBSCAN(metric='euclidean', cluster_selection_method='leaf', prediction_data=True)

                                # Load the bertopic model, set the clustering model to the one created above
                                model = BERTopic(hdbscan_model = clustering_model, calculate_probabilities= True)   
                            
                            else: 
                                # Otherwise, use the default clustering model embeded in bertopic
                                model = BERTopic(calculate_probabilities= True)  

                            # Process the data stored in the database so that the bertopic model can handle the structure
                            new_list = []
                            for i in doc['responses']:
                                new_list+=(list(i.values()))                    

                            # Remove the empty strings in the data (which happens when a participant doesn't end up using all the responses)
                            new_list = [x for x in new_list if x]

                            # Start finding pattern in the data using the model 
                            try:
                                pred, prob = model.fit_transform(new_list)
                                # Manually lower the threshold of probabilty assignment
                                threshold = 0.3
                                for document in np.where(np.array(pred) == -1)[0]:
                                    if max(prob[document]) >= threshold:
                                        pred[document] = int(np.where(prob[document] == max(prob[document]))[0])
                                
                                # Animation for surprises and shows the state of the app.
                                st.success('Here you go! 🤟')
                                st.balloons()

                            # If it doesnt't work, show users what the potential problem might be 
                            except:
                                st.write('The model could not find clusters. This could be because the datasize is too small or because there is only one topic')

                            

                        
                        clustering_results = [] # Record the clustering results to store it into the database
                        downloadable_results = pd.DataFrame() # Record the clustering results to allow donwloading. Firebase have a particular format that it takes, so I created another variable to save the data for downloading
                        blank_rows = pd.DataFrame([['', ''],['', ''],['Next Cluster Starts','']]) # This is created to separate the clusters in the CSV file for better viewing

                        st.write('## The patterns in your data.\n')

                        # Instruction for users to interpret the results
                        with st.expander("Interpret the results"):
                            st.write('''The model has found some pattern in your data.
                                    Each cluster contains participants responses that the model considers to be similar
                                    The **Probability** column shows you how probable does that response belong to the assigned cluster.
                                    For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                                    ''')
                            st.image("Example - Interpretation.png")

                        
                        # Identify the number of clusters to display. Distinguished by whether there are data that doesn't have a cluster (-1)
                        if -1 in pred:
                            num_cluster = len(model.get_topic_info())-1
                        else: 
                            num_cluster = len(model.get_topic_info())

                        # Display each clusters            
                        for i in range(num_cluster):                
                            st.write(f'### Cluster {i+1}')
                            
                            # Find the index of the documents that belong to the cluster 
                            topic_index = np.where(np.array(pred) == i)

                            # Store the documents in an array
                            a_cluster = np.array(new_list)[topic_index]

                            # Store the probability vector (to belong in different cluster) of each document into another array
                            document_prob = np.array(prob)[topic_index]


                            if type(document_prob[0]) == float or type(document_prob[0]) == int :
                                max_doc_prob = document_prob

                            # If there are more than one cluster, then take the max value out of the probability vector. 
                            # This value would be the probability for that document to belong to the cluster it is assigned to
                            else:
                                max_doc_prob = document_prob.max(axis=1)
                            
                            # Store the documents and the probability into the dataframe for display 
                            df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                            df = df.sort_values('Probability', ascending= False)

                            # Store the documents and the probability into the dataframe for downloading
                            downloadable_results = downloadable_results.append(blank_rows) 
                            downloadable_results =downloadable_results.append(df)


                            # Display the most relevant document.
                            st.table(df.head())

                            # Allow users to see the rest of the responses in the cluster if they want to 
                            with st.expander("View More Responses in this Cluster"):
                                st.table(df.iloc[5:])

                            # Converting the dataframe into a form that is storable on firebase
                            lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                            lst_storage = lst_storage.tolist()
                            dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                            cluster_dict = dict(zip(dictionary_keys, lst_storage))
                            clustering_results.append(cluster_dict)

                        
                        # Displaying the documents that don't have a cluster 
                        if -1 in pred:
                            st.write("### Here are the responses that the model couldn't find a cluster for")

                            # Find the index of the documents that doesn't have a cluster 
                            topic_index = np.where(np.array(pred) == -1)

                            # Store the documents in an array
                            a_cluster = np.array(new_list)[topic_index]

                            # Store the probability vector (to belong in different cluster) of each document into another array
                            document_prob = np.array(prob)[topic_index]
                            
                            if type(document_prob[0]) == float or type(document_prob[0]) == int :
                                max_doc_prob = document_prob

                            # If there are more than one cluster, then take the max value out of the probability vector. 
                            # This value would be the probability for that document to belong to the cluster it is assigned to
                            else:
                                max_doc_prob = document_prob.max(axis=1)

                            # Store the documents and the probability into the dataframe for display 
                            df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                            df = df.sort_values('Probability', ascending= False)

                            # Store the documents and the probability into the dataframe for downloading
                            blank_rows_2 = pd.DataFrame([['', ''],['', ''],['Responses with No Cluster','']])
                            downloadable_results = downloadable_results.append(blank_rows) 
                            downloadable_results =downloadable_results.append(df)
                            st.table(df)

                            # Converting the dataframe into a form that is storable on firebase
                            lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                            lst_storage = lst_storage.tolist()
                            dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                            cluster_dict = dict(zip(dictionary_keys, lst_storage))
                            clustering_results.append(cluster_dict)

                            # Tell the system that this room has data that doesn't have a cluster
                            # So that when it is being called by the participants, the system would dael accordingly
                            doc_ref.update({
                                "no_cluster":  True,
                            })

                        # Store the clustering results into the database
                        try:
                            # remove the existing results first
                            doc_ref.update({
                                "clustering_results":  [],
                            })

                            # Store the updated results
                            doc_ref.update({
                                "clustering_results":  clustering_results,
                            })
                        except:
                            st.write('Cannot write the results')

                        # Allow downloading the clustering in CSV files
                        csv = downloadable_results.to_csv().encode('utf-8')
                        st.download_button("Download your clustering data",  csv, 'Cluster Results from findPattern.csv')
                        
            except:
                st.write('')

    except:
        try: 
            # The room number is default to 0
            if room_number ==0 :
                st.write("Enter your room number 👋")
            else:
                 # If it's an invalud room number 
                st.write("Please enter a valid room number 🙏")

        except:
            # If it's an invalud room number 
            st.write("Please enter a valid room number 🙏")

###########################################################
### State 4: Participants #################################
###########################################################

elif user_mode == "Participant":

    try:
        # Create the room_number input 
        room_number = st.text_input('Room Number', value = 0)
    except:
        pass

    try:
        # Connect with the database and get the data based on the room number 
        doc_ref = db.collection("Room").document(f"Room {room_number}")
        doc = doc_ref.get()
        doc = doc.to_dict()
        prompt_name = doc['prompt_question'] 
        prompt_description = doc['prompt_description']
        number_of_response = doc["num_response"]

        # Display room information
        st.write(f"### 🙃 Prompt: {prompt_name}")
        st.write(prompt_description)

        # create a dictionary to keep track of all the responses by one participant
        all_response = []

        with st.expander("Reminder for before you start"):
            st.write("For the model to work, please provide one idea per response box. For example, if the prompt is 'what do you want to eat for breakfast', and your response is 'milk and bread', you should put 'milk' and 'bread' in separate response box.")

        # Create a form for the participant to fill out their responses
        with st.form("This form"):
            
            # Create a dictionary of response for each participant
            numberlist = [f'response {nr}' for nr in range(number_of_response)]
            response_list = dict.fromkeys(numberlist)
            st.write(f"### Your Response")
            # Create text field for participants to respond and save the responses to the dictionary
            for i in range(number_of_response):
                response_list[f'response {i}'] = st.text_input(f'Response {i+1}')
            
            # Append the responses to the list
            all_response.append(response_list)
    
            submitted = st.form_submit_button("Submit")
            ss_submit = SessionState.get(submitted = False) 

            if submitted:
                ss_submit.submitted = True
                st.write("Thank you for your input 👍")
                
        
        # If the facilitator allows the participants to see each other responses
        if doc["cross_pollination"]:

            # Create a button for viewing participants responses
            # Since the real-time update function is not well supported for Python on Firebase,
            # I worked around this by allowing users to see update everytime they click the button
            st.write("## 📝 Participant Response")
            view_responses = st.button("View other participants' responses")
            ss10 = SessionState.get(view_responses = False) 
            
            logging.info('nihao')

            if view_responses:
                ss10.view_responses = True
            
            logging.info('2')
            try:
                if ss10.view_responses == True:

                    # If there is no responses yet, show the status.
                    if doc['responses'] == []:
                        st.write("No response submitted yet")

                    # Otherwise, show the responses
                    else:
                        st.table(doc['responses'])
            except:
                pass
            
            logging.info('3')

        try:
            # Update the responses into the database
            if ss_submit.submitted:
        
                
                # If the room still accepts response
                if doc["collect_response"] == True:
                    # Append the responses to the database
                    current_response = doc['responses']
                    updated_response = current_response + all_response
                    n = 0

                    # Dealing with the sitaution when more than one participant wants to submit
                    # n is set to avoid infinite looping. 5 should be sufficient for avoiding simultaenous updates
                    while all_response[0] not in doc["responses"] and n<5:
                        doc_ref.update({
                            "responses": updated_response,
                        })
                        
                        # The time is used to create a buffer time between each updates
                        time.sleep(1)
                        doc = doc_ref.get()
                        doc = doc.to_dict()
                        current_response = doc['responses']
                        updated_response = current_response + all_response
                        n+=1

                # Allow participants to view the clustering results
                st.write('## 🧩 Find Patterns')
                see_results = st.button('See Clustering Results')
        

            if see_results:
                if doc['clustering_results'] == []:
                    st.write('There is no results yet. Check back later.')
                else:
                    st.balloons()

                    # Instruction for users to interpret the results                    
                    with st.expander("Interpret the results"):
                        st.write('''The model has found some pattern in your data.
                            Each cluster contains participants responses that the model considers to be similar
                            The **Probability** column shows you how probable does that response belong to the assigned cluster.
                            For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                            ''')
                        st.image("Example - Interpretation.png")
                    
                    
                    st.write('## The patterns in the ideas\n')

                    # Display each clusters            
                    for c_id in range(len(doc['clustering_results'])):
                        
                        # For the 0 to n-1 clusters, they will definitely be meaningful clusters
                        if c_id <len(doc['clustering_results'])-1:
                            st.write(f'### Cluster {c_id+1}')
                        
                        # For the last cluster, depending on the types of room, 
                        else:
                            # room that do have a data that don't have a cluster
                            if doc['no_cluster'] == True: 
                                st.write("### Here are the responses that the model couldn't find a cluster for")
                            # room that don't have a data that don't have a cluster
                            else: 
                                st.write(f'### Cluster {c_id+1}')
                        
                        # Take the data from the database and process them in a way that is displayable on streamlit
                        display = np.array(list(dict.values(doc['clustering_results'][c_id])))
                        display = pd.DataFrame(display, columns = ['Response', 'Probability'])
                        display = display.sort_values('Probability', ascending= False)
                        
                        # Display the most relevant document.
                        st.table(display.head()) 

                        # Allow users to see the rest of the responses in the cluster if they want to 
                        with st.expander ("View More Responses in this Cluster"):
                            st.table(display)

        except:
            pass

    except:
        try:  
            # The room number is default to 0
            if room_number ==0 :
                st.write("Enter your room number 👋")
            else: 
                 # If it's an invalud room number 
                st.write("Please enter a valid room number 🙏")

        except:
            # If it's an invalud room number 
            st.write("Please enter a valid room number 🙏")

    