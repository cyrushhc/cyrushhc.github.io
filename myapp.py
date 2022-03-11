from re import L
from scipy.misc import ascent
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
import logging

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


user_mode = st.selectbox('Who are you?', ['-','Facilitator (Create New Room)','Facilitator (Go to Existing Room)','Participant'])

if user_mode == '-':
    st.write('## Welcome to findPattern.')
    st.write('findPattern is a machine learning-powered tool that helps people conduct affinity mapping exercise among a larger crowd FASTER.') 
    st.write("Whether you  are a product person who want to work with users to identify the common pain points they have, or a conference speaker who want to ask your audience what they associate a brand with, or maybe your are a professor asking students to provide feedback for the course to revamp education together, findPattern is here for you.")
    st.write('findPattern uses state-of-the-art Natural Language Processing technique--BERT to understand and process a huge number of texts faster than a human brain could do.')

    with st.expander("What is affinity mapping and why use it?"):
        st.write("Affinity mapping is the processing of taking a bunch of qualitative information, often about users, and group them into categories by similarities.")
        st.image('https://marketing.invisionapp-cdn.com/cms/images/lr1orcar/marketing-pages/c9bb16e5cfa670bfcd5c07ef4e126097958fb4f2-2880x1444.png?w=2880&fm=jpg&q=90', "An exmaple of affinity mapping.")
        st.write("[Image Source: Invision](https://www.invisionapp.com/freehand/templates/detail/affinity-diagram-template)")
    
    with st.expander("How does the app work?"):
        st.image('How it Works.png')


    with st.expander("How this app find patterns using algorithm?"):
        st.write('BERtopic is a Python library that lets us do topic modeling (topic modeling is the machine learning jargon for finding topics within text without telling the machine what kind of topics there might be) created by Maarten Grootendorst. BERTopic combines a handful of useful existing python libraries, inlcuding a text encoder (SentenceTransformer), a dimension reduction tool (UMAP), and a clustering tool (HDBSCAN). So what are these python libraries doing and why does combining them help us do topic modeling? ')
        st.write('### Encoder -- SentenceTransformer')
        st.write('A text encoder reads the text input, considers the context and meaning of words in the text input, and represents text input in probability, which we call word embeddings. An example of the word embeddings is below. Each word is represented as a vector of 50 values in the GloVe model. Each of the values indicates a property of the word.')
        st.image('https://github.com/cyrushhc/findPattern/blob/main/Encoding%20exmaple.png?raw=true')
        st.write('Image Source: Jay Alammar:https://jalammar.github.io/illustrated-word2vec/')

        st.write('This is where the powerful BERT comes in: BERT is a empirically powerful encoder that produces state of the art results (Devlin et al., 2019; Thompson & Mimno, 2020). The SentenceTransformers library in Python uses BERT as encoder (Reimers & Gurevych, 2019). BERT can be extended to achieve several tasks to understand and process natural language. One such example is BERTopic.')
        st.write('### Reduce Dimenstion -- UMAP')
        st.write('As mentioned before, after encoding each response (it could be a document, a sentence, or a word), each response will be represented in a list of numbers. To be exact, for SentenceTransformer encoder, each response would be represented with a list of 768 numbers. And this is a large number of dimensions for the computer to process! Large dimensions requires more time and computational resource to process. Moreover, not every dimension would be useful in separating responses into clusters. For example, if we have four words, [cats, dogs, girls, boys] and that one of the dimension is whether the text is a living object, then all four text would be very similar in that respect––making that dimension less useful. This is why we reduce dimension with UMAP. UMAP is also an powerful dimension-reduction techqniques that preserve the high dimensional structure very well after reducing dimensions. After the reduction, the list of 768 values becomes a list of 5 values. This is so that you do not have to wait forever for the results to show!')
        st.write('### Clustering - HDBSCAN')
        st.write('The last step of the BERTopic library is the clustering step. BERTopic uses HDBSCAN, which is a model that identifies clusters by the density of the data points, which is similar to the way human eyes identify clusters. Here is a great video telling you how HDBSCAN clusters datapoints.')
        st.image('HDBSCAN.gif')



elif user_mode == "Facilitator (Create New Room)":
    
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
            st.code(f"👉 Join here https://share.streamlit.io/cyrushhc/findpattern/main/myapp.py\n🚪 Room number: {ss_r.room_number}")
            
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
                    "no_cluster": False,
                })
                ss_init.initial_state += 1
            
            with st.expander("View Participant Interface"):
                st.image("https://github.com/cyrushhc/cyrushhc.github.io/blob/main/Example.png?raw=true")
    except: 
        st.write('')
        
    

    try:
        print(ss_r.room_number)
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
            with st.expander("How to choose a setting"):
                st.write("I would reommend going with `generic` first. If you find that the results are too generic, then choose `nuanced`.")
                st.write("When you choose `generic`, the model is going to lump together smaller clusters that are simliar.")
                st.write("When you choose `nuanced`, the model would show you the smaller clusters before they are lumped together.")

            result_fidelity = st.radio("Do you want more a more nuanced results or a more high-level generic clustering resutls?", ['Nuanced', 'Generic'])
            find_pattern = st.button("Find Pattern")
            ss4 = SessionState.get(find_pattern = False) 

            # if find_pattern:
            #     ss4.find_pattern = True

                
            if find_pattern == True:
                with st.spinner('Finding patterns in your data...'):
                    if result_fidelity == 'Nuanced':
                        clustering_model = HDBSCAN(metric='euclidean', cluster_selection_method='leaf', prediction_data=True)
                        model = BERTopic(hdbscan_model = clustering_model, calculate_probabilities= True)   
                    
                    else: 
                        model = BERTopic(calculate_probabilities= True)  

                    new_list = []
                    for i in doc['responses']:
                        new_list+=(list(i.values()))                    

                    new_list = [x for x in new_list if x]

                    try:
                        pred, prob = model.fit_transform(new_list)

                    except:
                        st.write('The model could not find clusters. This could be because the datasize is too small or because there is only one topic')

                    # Manually lower the threshold of probabilty assignment
                    threshold = 0.3
                    for document in np.where(np.array(pred) == -1)[0]:
                        if max(prob[document]) >= threshold:
                            pred[document] = int(np.where(prob[document] == max(prob[document]))[0])

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


                if -1 in pred:
                    num_cluster = len(model.get_topic_info())-1
                else: 
                    num_cluster = len(model.get_topic_info())

                
                for i in range(num_cluster):                
                    st.write(f'### Cluster {i+1}')
                    
                    topic_index = np.where(np.array(pred) == i)
                    a_cluster = np.array(new_list)[topic_index]
                    document_prob = np.array(prob)[topic_index]

                    # st.write("this is doc prob:", document_prob)

                    if type(document_prob[0]) == float or type(document_prob[0]) == int :
                        st.write("int")
                        max_doc_prob = document_prob
                    else:
                        max_doc_prob = document_prob.max(axis=1)
                        
                    df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])

                    df = df.sort_values('Probability', ascending= False)

                    st.table(df)

                    lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                    logging.info(lst_storage)
                    logging.info(lst_storage[0])

                    lst_storage = lst_storage.tolist()


                    dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
        
                    cluster_dict = dict(zip(dictionary_keys, lst_storage))

                    
                    # Trying to turn the results into dictionary so I can store it on Firestore
                    
                    logging.info(cluster_dict)
                    clustering_results.append(cluster_dict)

                
                
                if -1 in pred:
                    st.write("### Here are the responses that the model couldn't find a cluster for")

                    topic_index = np.where(np.array(pred) == -1)
                    a_cluster = np.array(new_list)[topic_index]
                    document_prob = np.array(prob)[topic_index]
                    max_doc_prob = document_prob.max(axis=1)

                    df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                    df = df.sort_values('Probability', ascending= False)

                    st.table(df)


                    lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                    lst_storage = lst_storage.tolist()

                    dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                    cluster_dict = dict(zip(dictionary_keys, lst_storage))
                    

                    clustering_results.append(cluster_dict)
                    doc_ref.update({
                        "no_cluster":  True,
                    })

                try:
                    doc_ref.update({
                        "clustering_results":  [],
                    })
                    doc_ref.update({
                        "clustering_results":  clustering_results,
                    })
                except:
                    st.write('Cannot write the results')
                
                

    except:
        st.write('')
    
elif user_mode == 'Facilitator (Go to Existing Room)':
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
        st.write(f"### 🙃 Prompt: {prompt_name}")
        st.write(prompt_description)
        goal = st.radio('What do you want to do?',['See existing results', 'Create new cluster results'])
        
        if goal == "See existing results":
            if doc['clustering_results'] == []:
                st.write('There is no results yet. Check back later.')
            else:
                with st.expander("Interpret the results"):
                    st.write('''The model has found some pattern in your data.
                        Each cluster contains participants responses that the model considers to be similar
                        The **Probability** column shows you how probable does that response belong to the assigned cluster.
                        For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                        ''')
                    st.image("https://github.com/cyrushhc/findPattern/blob/main/Example%20-%20Interpretation.png?raw=true")
                st.write('## The patterns in the ideas\n')

                for c_id in range(len(doc['clustering_results'])):
                    
                    if c_id <len(doc['clustering_results'])-1:
                        st.write(f'### Cluster {c_id+1}')
                    
                    else:
                        if doc['no_cluster'] == True: 
                            st.write("### Here are the responses that the model couldn't find a cluster for")
                        else: 
                            st.write(f'### Cluster {c_id+1}')
                    
                    display = np.array(list(dict.values(doc['clustering_results'][c_id])))
                    display = pd.DataFrame(display, columns = ['Response', 'Probability'])

                    display = display.sort_values('Probability', ascending= False)

                    st.table(display)

        else: 
            st.write("## 📝 Participant Response")
            seeresult = st.button("View Results")
            ss2 = SessionState.get(seeresult = False) 
            
            logging.info(ss2.seeresult)

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

            
            logging.info("end_collection")  
            if ss3.end_collection == True:
                doc_ref.update({
                    "collect_response": False,
                    "ready_to_cluster": True,
                }
                )
                logging.info("Update success")

            logging.info("end_collection")
            try:    
                if doc['ready_to_cluster'] == True:
                    st.write('## 🧩 Find Patterns')
                    with st.expander("How to choose a setting"):
                        st.write("I would reommend going with `generic` first. If you find that the results are too generic, then choose `nuanced`.")
                        st.write("When you choose `generic`, the model is going to lump together smaller clusters that are simliar.")
                        st.write("When you choose `nuanced`, the model would show you the smaller clusters before they are lumped together.")

                    result_fidelity = st.radio("Do you want more a more nuanced results or a more high-level generic clustering resutls?", ['Nuanced', 'Generic'])
                    find_pattern = st.button("Find Pattern")
                    ss4 = SessionState.get(find_pattern = False) 

                    # if find_pattern:
                    #     ss4.find_pattern = True

                        
                    if find_pattern == True:
                        with st.spinner('Finding patterns in your data...'):
                            if result_fidelity == 'Nuanced':
                                clustering_model = HDBSCAN(metric='euclidean', cluster_selection_method='leaf', prediction_data=True)
                                model = BERTopic(hdbscan_model = clustering_model, calculate_probabilities= True)   
                            
                            else: 
                                model = BERTopic(calculate_probabilities= True)  

                            new_list = []
                            for i in doc['responses']:
                                new_list+=(list(i.values()))                    

                            new_list = [x for x in new_list if x]

                            try:
                                pred, prob = model.fit_transform(new_list)

                            except:
                                st.write('The model could not find clusters. This could be because the datasize is too small or because there is only one topic')

                            # Manually lower the threshold of probabilty assignment
                            threshold = 0.3
                            for document in np.where(np.array(pred) == -1)[0]:
                                if max(prob[document]) >= threshold:
                                    pred[document] = int(np.where(prob[document] == max(prob[document]))[0])

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


                        if -1 in pred:
                            num_cluster = len(model.get_topic_info())-1
                        else: 
                            num_cluster = len(model.get_topic_info())

                        
                        for i in range(num_cluster):                
                            st.write(f'### Cluster {i+1}')
                            
                            topic_index = np.where(np.array(pred) == i)
                            a_cluster = np.array(new_list)[topic_index]
                            document_prob = np.array(prob)[topic_index]

                            # st.write("this is doc prob:", document_prob)

                            if type(document_prob[0]) == float or type(document_prob[0]) == int :
                                st.write("int")
                                max_doc_prob = document_prob
                            else:
                                max_doc_prob = document_prob.max(axis=1)
                                
                            df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                            df = df.sort_values('Probability', ascending= False)

                            st.table(df)

                            lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                            logging.info(lst_storage)
                            logging.info(lst_storage[0])

                            lst_storage = lst_storage.tolist()


                            dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                
                            cluster_dict = dict(zip(dictionary_keys, lst_storage))
                            
                            # Trying to turn the results into dictionary so I can store it on Firestore
                            
                            logging.info(cluster_dict)
                            clustering_results.append(cluster_dict)

                        
                        
                        if -1 in pred:
                            st.write("### Here are the responses that the model couldn't find a cluster for")

                            topic_index = np.where(np.array(pred) == -1)
                            a_cluster = np.array(new_list)[topic_index]
                            document_prob = np.array(prob)[topic_index]
                            max_doc_prob = document_prob.max(axis=1)

                            df = pd.DataFrame({'Response': a_cluster, 'Probability': max_doc_prob}, columns=['Response', 'Probability'])
                            df = df.sort_values('Probability', ascending= False)
                            st.table(df)


                            lst_storage = np.stack((a_cluster, max_doc_prob), axis=-1)
                            lst_storage = lst_storage.tolist()

                            dictionary_keys = [f'entry {num}' for num in range(len(a_cluster))]
                            cluster_dict = dict(zip(dictionary_keys, lst_storage))
                            

                            clustering_results.append(cluster_dict)

                            doc_ref.update({
                                "no_cluster":  True,
                            })

                        try:
                            doc_ref.update({
                                "clustering_results":  [],
                            })
                            logging.info(clustering_results)
                            doc_ref.update({
                                "clustering_results":  clustering_results,
                            })
                        except:
                            st.write('Cannot write the results')
                        
            except:
                st.write('')
        
    except:
        try:  
            if room_number ==0 :
                st.write("Enter your room number 👋")
            else:
                pass
                # st.write("Please enter a valid room number 🙏")
        except:
            st.write("Please enter a valid room number 🙏")

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

                if doc["collect_response"] == True:
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

                    with st.expander("Interpret the results"):
                        st.write('''The model has found some pattern in your data.
                            Each cluster contains participants responses that the model considers to be similar
                            The **Probability** column shows you how probable does that response belong to the assigned cluster.
                            For example, the below result reads:  The response `Banana` has a `0.6694 probability` to belong to the `cluster 3`. 
                            ''')
                        st.image("https://github.com/cyrushhc/findPattern/blob/main/Example%20-%20Interpretation.png?raw=true")
                    st.write('## The patterns in the ideas\n')
                    for c_id in range(len(doc['clustering_results'])):
                        
                        if c_id <len(doc['clustering_results'])-1:
                            st.write(f'### Cluster {c_id+1}')
                        
                        else:
                            if doc['no_cluster'] == True: 
                                st.write("### Here are the responses that the model couldn't find a cluster for")
                            else: 
                                st.write(f'### Cluster {c_id+1}')
                        
                        display = np.array(list(dict.values(doc['clustering_results'][c_id])))
                        display = pd.DataFrame(display, columns = ['Response', 'Probability'])
                        display = display.sort_values('Probability', ascending= False)
                        st.table(display)

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

    