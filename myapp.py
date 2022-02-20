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
from bertopic import BERTopic
import random
from hdbscan import HDBSCAN

# Authenticate to Firestore with the JSON account key.
import json
key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)

db = firestore.Client(credentials=creds, project="automatic-affinity-mapping")




with open("style.css") as f:  
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


st.write("# findPattern.")

# Add Rooms
def room_number_generator():
    return random.randint(1,1000)


user_mode = st.selectbox('Who are you?', ['-','Facilitator','Participant'])

if user_mode == '-':
    st.write('')

elif user_mode == "Facilitator":
    
    st.write("## ✋ Discussion Prompt")
    prompt_name = st.text_input('Prompt')
    prompt_description = st.text_input('What kind of response do you want participants to give? (e.g. each response should be 1-2 sentence.)')
    number_of_response = st.slider(label ='Number of responses for each participant', min_value = 0, max_value = 20, value = 5, step = 5) 
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
            st.write("**Copy-paste and share** this invite info with your participants")
            st.code(f"👉 Join here https://tinyurl.com/findpatterns\n🚪 Room number: {ss_r.room_number}")
            
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
            
            with st.expander("View Participant Interface"):
                st.image("https://github.com/cyrushhc/cyrushhc.github.io/blob/main/Example.png?raw=true")
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
            result_fidelity = st.radio("Do you want more a more nuanced results or a more high-level generic clustering resutls?", ['Nuanced', 'Generic'])
            find_pattern = st.button("Find Pattern")
            ss4 = SessionState.get(find_pattern = False) 

            

            if find_pattern:
                ss4.find_pattern = True

                
            if ss4.find_pattern == True:
                with st.spinner('Finding patterns in your data...'):
                    
                    if result_fidelity == 'Nuanced':
                        clustering_model = HDBSCAN(metric='euclidean', cluster_selection_method='leaf', prediction_data=True)
                        model = BERTopic(hdbscan_model = clustering_model, calculate_probabilities= True)
                    
                    else: 
                        model = BERTopic()

                    new_list = []
                    for i in doc['responses']:
                        new_list+=(list(i.values()))                    
                    pred, prob = model.fit_transform(new_list)
                    st.success('Here you go! 🤟')
                    st.balloons()
                
                clustering_results = []
                st.write('## The patterns in your data.\n')

                with st.expander("Interpret the results"):
                    st.write('''The model has found some pattern in your data.
                            Each cluster contains participants responses that the model considers to be similar
                            The **Probability** column shows you how probable does that response belong to the assigned cluster.
                            For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                            ''')
                    st.image("https://github.com/cyrushhc/findPattern/blob/main/Example%20-%20Interpretation.png?raw=true")
        
                for i in range(len(model.get_topic_info()) -1):                
                    st.write(f'### Cluster {i+1}')
                    
                    topic_index = np.where(np.array(pred) == i)
                    a_cluster = np.array(new_list)[topic_index]
                    document_prob = np.array(prob)[topic_index]
                    max_doc_prob = document_prob.max(axis=1)

                    df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])

                    st.table(df)

                    dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                    cluster_dict = dict(zip(dictionary_keys, a_cluster))

                    # Trying to turn the results into dictionary so I can store it on Firestore
                    
                    clustering_results.append(cluster_dict)

                # st.write(model.get_topic_info())

                st.write("### Here are the responses that the model couldn't find a cluster for")
                topic_index = np.where(np.array(pred) == -1)
                a_cluster = np.array(new_list)[topic_index]
                document_prob = np.array(prob)[topic_index]
                max_doc_prob = document_prob.max(axis=1)

                df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])

                st.table(df)

                dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                cluster_dict = dict(zip(dictionary_keys, a_cluster))





                try:
                    doc_ref.update({
                        "clustering_results":  clustering_results,
                    })
                except:
                    st.write('Cannot write the results')
                

    except:
        st.write('')

    



elif user_mode == "Participant":

    try:
        # Create the room_number input 
        room_number = int(st.text_input('Room Number', value = 0))
    except:
        pass

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
            
            # Create a dictionary of response for each participant
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

        try:
            if ss_submit.submitted:
                
                current_response = doc['responses']
                updated_response = current_response + all_response

                n = 0
            
                # Dealing with the sitaution when more than one participant wants to submit
                while all_response[0] not in doc["responses"] and n<5:
                    doc_ref.update({
                        "responses": updated_response,
                    })
                    time.sleep(1)
                    doc = doc_ref.get()
                    doc = doc.to_dict()
                    current_response = doc['responses']
                    updated_response = current_response + all_response
                    n+=1

                st.write("Thank you for your input 👍")
                see_results = st.button('See results')
        


            if see_results:
                if doc['clustering_results'] == []:
                    st.write('There is no results yet. Check back later.')
                else:
                    st.balloons()
                    st.write('## The patterns in the ideas\n')
                    for c_id in range(len(doc['clustering_results'])):
                        st.write(f'### Cluster {c_id+1}')
                        st.table(np.array(list(dict.values(doc['clustering_results'][c_id]))))

        except:
            pass

    except:
        try:  
            if room_number ==0 :
                st.write("Enter your room number 👋")
            else:
                st.write("Please enter a valid room number 🙏")
        except:
            st.write("Please enter a valid room number 🙏")

    