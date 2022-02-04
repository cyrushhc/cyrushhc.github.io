from re import L
import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
import random
import SessionState
import pandas as pd 
import time
from st_aggrid import AgGrid 
import numpy as np

# Authenticate to Firestore with the JSON account key.
import json
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="automatic-affinity-mapping")

from bertopic import BERTopic


with open("style.css") as f:  
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


st.write("# findPattern.")

# Add Rooms
def room_number_generator():
    return random.randint(1,1000)

# def create_response(number_of_response, participant_data):
#         """
#         participant_data: could either be the number of participant or the name
#         number_of_response: number of response for each participant
#         """
#         if type(participant_data) == int:
            
#             # create a dictionary to keep track of all the response
#             all_response = []

#             # Create a for loop to create all the response
#             for respondant in range(participant_data):

#                 with st.form(f"{respondant}"):

#                     numberlist = [f'response {nr}' for nr in range(number_of_response)]
#                     response_list = dict.fromkeys(numberlist)
#                     st.write(f"### Your Response")
#                     for i in range(number_of_response):
#                         response_list[f'response {i}'] = st.text_input(f'Response {i+1}')
                    
#                     all_response.append(response_list)
                    
#                     submitted = st.form_submit_button("Submit")

#             return all_response, submitted


user_mode = st.selectbox('Who are you?', ['-','Facilitator','Participant'])

if user_mode == '-':
    st.write('')

elif user_mode == "Facilitator":
    
    st.write("## ✋ Discussion Prompt")
    prompt_name = st.text_input('Prompt')
    prompt_description = st.text_input('Prompt description (optional)')
    number_of_response = st.slider(label ='Number of responses for each participant', min_value = 0, max_value = 20, value = 3) 
    finish = st.button("Create a Room")
    ss = SessionState.get(finish = False)
    room_number = st.empty()
    ss_r = SessionState.get(room_number = None)

    initial_state = st.empty()
    ss_init = SessionState.get(initial_state = None)


    if finish:
        ss.finish = True
        ss_r.room_number = room_number_generator()
        ss_init.initial_state = 0

    try : 
        if ss.finish:
            st.write("")
            st.write("\n")
            st.write(f"## 🔗 Room Number: {ss_r.room_number}")
            st.write("Copy-Paste this invite info for your participants")
            st.code(f"👋 Invite Info\nJoin the discussion at https://tinyurl.com/findpatterns\nRoom number: {ss_r.room_number}.")
            doc_ref = db.collection("Room").document(f"Room {ss_r.room_number}")
            if ss_init.initial_state == 0:
                doc_ref.set({
                    "prompt_question": prompt_name,
                    "prompt_description":prompt_description,
                    "responses": [],
                    "room_number": ss_r.room_number,
                    "num_response":number_of_response, 
                    "collect_response": True,
                    "ready_to_cluster": False,
                    'clustering_results': [],
                })
                ss_init.initial_state += 1
    except: 
        st.write('')
        
    

    try:    
        doc_ref = db.collection("Room").document(f"Room {ss_r.room_number}") 
        st.write("## 📝 Participant Response")
        doc = doc_ref.get().to_dict()  
        seeresult = st.button("View Results")
        ss2 = SessionState.get(seeresult = False) 
        
        if seeresult:
            ss2.seeresult = True

        if ss2.seeresult == True:
            if doc['responses'] == []:
                st.write("No response submitted yet")
            else:
                st.write(doc['responses'])
        
        end_collection = st.button("Close Participant Response")
        ss3 = SessionState.get(end_collection = False) 

        if end_collection:
            ss3.end_collection = True

        if ss3.end_collection == True:
            doc_ref.update({
                "collect_response": False,
                "ready_to_cluster": True,
            }
            )
            
    except:
        st.write("")    

    try:    
        doc_ref = db.collection("Room").document(f"Room {ss_r.room_number}") 
        doc = doc_ref.get().to_dict()
        if  doc['ready_to_cluster'] == True:
            st.write('## 🧩 Find Patterns')
            find_pattern = st.button("Find Pattern")
            ss4 = SessionState.get(find_pattern = False) 

            if find_pattern:
                ss4.find_pattern = True

            if ss4.find_pattern == True:
                with st.spinner('Finding patterns in your data...'):
                    
                    model = BERTopic()
                    new_list = []
                    for i in doc['responses']:
                        new_list+=(list(i.values()))                    
                    pred, prob = model.fit_transform(new_list)
                    st.success('Here you go! 🤟')
                    st.balloons()
                
                clustering_results = []
                st.write('## The patterns in your data.\n')
                for i in range(len(model.get_topic_info())):
                    st.write(f'### Cluster {i}')
                    topic_index = np.where(np.array(pred) == i)
                    a_cluster = np.array(new_list)[topic_index]
                    st.table(a_cluster)

                    dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                    cluster_dict = dict(zip(dictionary_keys, a_cluster))

                    # Trying to turn the results into dictionary so I can store it on Firestore
                    
                    clustering_results.append(cluster_dict)

                # st.write(model.get_topic_info())

                try:
                    doc_ref.update({
                        "clustering_results":  clustering_results,
                    })
                except:
                    st.write('Cannot write the results')
                    


                # data = {'Response': ['apple', 'banana', 'grapes', 'orange'], 'Person': ['Cyrus', 'Kate','Cyrus', 'James']}  
                # df1 = pd.DataFrame(data)
                # AgGrid(df1, theme='streamlit')

                # st.write('\n')

                # st.write('### Cluster 2')
                # data2 = {'Response': ['cats', 'dogs', 'monkeys', 'gorillas'], 'Person': ['Jimmy', 'James','Cyrus', 'Kenn']}  
                # df2 = pd.DataFrame(data2)
                # st.table(df2)
                

    except:
        st.write('')

    

    



# st.write("## 👀 View Mode")
# mode = st.radio(label = "Choose a mode", options= ["Response","Result"])

elif user_mode == "Participant":
    
    # initial_state = st.empty()
    # ss_init = SessionState.get(initial_state = None)
    
    
    # For some reasons I cannot use the stream() method 
    # It says that 'CollectionReference' object has no attribute 'stream'
    # room_ref = db.collection(u'Room')
    # room_id_list = []
    # st.write(room_ref.stream())
    # for rooms in room_ref.stream():
    #     room_id_list = [rooms.to_dict()['room_number']] 
    try:
        room_number = int(st.text_input('Room Number', value = 0))
    except:
        pass

    # if room_number != 0:
    try:
        doc_ref = db.collection("Room").document(f"Room {room_number}")
        doc = doc_ref.get()
        doc = doc.to_dict()
        prompt_name = doc['prompt_question'] 
        prompt_description = doc['prompt_description']
        number_of_response = doc["num_response"]
        st.write(f"### 🙃 Prompt: {prompt_name}")
        st.write(prompt_description)

        # create a dictionary to keep track of all the response
        all_response = []

        # Create a for loop to create all the response
        with st.form("This form"):
            numberlist = [f'response {nr}' for nr in range(number_of_response)]
            response_list = dict.fromkeys(numberlist)
            st.write(f"### Your Response")
            for i in range(number_of_response):
                response_list[f'response {i}'] = st.text_input(f'Response {i+1}')
                
            all_response.append(response_list)
    
            submitted = st.form_submit_button("Submit")
            ss_submit = SessionState.get(submitted = False) 
            if submitted:
                ss_submit.submitted = True
                # ss_init.initial_state = 0

        # if create_participant == 'Enter Number of Participant':
        #     all_response = create_response(number_of_response, number_of_p)
            
        #     # create a form that will have a set number of response

        # elif create_participant == 'Enter Participant Name':
        #     p_name_list = p_name.split(",")
        #     all_response = create_response(number_of_response, p_name_list)
        try:
            if ss_submit.submitted:

                current_response = doc['responses']
                updated_response = current_response + all_response

                if doc['collect_response'] == True:
                    doc_ref.update({
                        "responses": updated_response,
                    })
                    st.write("Thank you for your input 👍")

                else:
                    st.write("You can only submit the response once 🙃")

                st.write("Please wait for the facilitator to get back to you before clicking the next button")
            
                see_results = st.button('See results')

                if see_results:
                    if doc['clustering_results'] == []:
                        st.write('There is no results yet. Check back later.')
                    else:
                        st.balloons()
                        st.write('## The patterns in the ideas\n')
                        for c_id in range(len(doc['clustering_results'])):
                            st.write(f'### Cluster {c_id}')
                            st.table(np.array(list(dict.values(doc['clustering_results'][c_id]))))
        except:
            st.write('')

    except:
        if room_number ==0 :
            st.write("Enter your room number 👋")
        else:
            st.write("Please enter a valid room number 🙏")

    