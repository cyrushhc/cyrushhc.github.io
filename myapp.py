
import streamlit as st
from google.oauth2 import service_account
from google.cloud import firestore
import random

# yoyo
# Authenticate to Firestore with the JSON account key.
import json

key_dict = json.loads(st.secrets["textkey"])
creds = service_account.Credentials.from_service_account_info(key_dict)
db = firestore.Client(credentials=creds, project="automatic-affinity-mapping")


#from sentence_transformers import SentenceTransformer, util
#model = SentenceTransformer('stsb-roberta-large')


with open("style.css") as f:  
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# Experiment with "Add a response" Button
  
    # I want to add a new input whenever users click the button but it would overwrite the previous response
    # Turns out you just can nest any action within the button 
    # https://docs.streamlit.io/library/api-reference/widgets/st.button
    # Therefore, to make it work, I'll just allow predefined number of questions

    # st.text_input(f'response {n}')
    # add = st.button("Add a response", key = n)
    # n+=1


    # if add:
    #     st.text_input(f'response {n}')
    #     add2 = st.button("Add another response")
    #     n+=1


    # if add2:
    #     st.text_input(f'response {n}')
    #     add3 = st.button("Add a response")
    #     n+=1  


st.sidebar.write("## ✋ The Prompt for Discussion")
prompt_name = st.sidebar.text_input('Prompt')
prompt_description = st.sidebar.text_input('Prompt description (optional)')
# Let users choose whether they want to create based on name or number of participant

create_participant = st.sidebar.radio('how would you like to create parcipant for this prompt?', ['Enter Number of Participant', 'Enter Participant Name'])

if create_participant == "Enter Participant Name":
    p_name = st.sidebar.text_input("Enter Partcipant Name (separated by comma ',' )", value = "{participant name}")
elif create_participant == 'Enter Number of Participant':
    number_of_p = st.sidebar.slider("Number of Participant",max_value = 20, value = 3) 

number_of_response = st.sidebar.slider(label ='Number of responses for each participant', min_value = 0, max_value = 20, value= 3) 


st.sidebar.write("## 👀 View Mode")
mode = st.sidebar.radio(label = "Choose a mode", options= ["Response","Result"])

def create_response(number_of_response, participant_data):
        """
        participant_data: could either be the number of participant or the name
        number_of_response: number of response for each participant
        """
        if type(participant_data) == int:
            
            # create a dictionary to keep track of all the response
            all_response = []
            

            # Create a for loop to create all the response
            for respondant in range(participant_data):

                with st.form(f"{respondant}"):

                    numberlist = [f'response {nr}' for nr in range(number_of_response)]
                    response_list = dict.fromkeys(numberlist)
                    st.write(f"### Participant {respondant+1}")
                    for i in range(number_of_response):
                        response_list[i] = st.text_input(f'Response {i+1}')
                    
                    all_response.append(response_list)
                    
                    st.form_submit_button("Submit")

            return all_response

        if type(participant_data) == list:

            # create a dictionary to keep track of all the response
            all_response = []

            # Create a for loop to create all the response
            for respondant in range(len(participant_data)):
                with st.form(f"{participant_data[respondant]}"):
                    
                    numberlist = [f'response {nr}' for nr in range(number_of_response)]
                    response_list = dict.fromkeys(numberlist)
                    st.write(f"### {participant_data[respondant]}")
                    for i in range(number_of_response):
                        response_list[i] = st.text_input(f'Response {i+1}')
                    
                    all_response.append(response_list)
                    
                    st.form_submit_button("Submit")
                    
            return all_response



if mode == "Response":

    st.write(f"### 🙃 Prompt: {prompt_name}")
    st.write(prompt_description)

    if create_participant == 'Enter Number of Participant':
        all_response = create_response(number_of_response, number_of_p)
        
        # create a form that will have a set number of response

    elif create_participant == 'Enter Participant Name':
        p_name_list = p_name.split(",")
        all_response = create_response(number_of_response, p_name_list)
        

    st.write(all_response)
    st.write(type(all_response))

finish = st.button("Done")

def room_number_generator():
    return random.randint(1,1000)

if finish:

    room_number = room_number_generator()

    doc_ref = db.collection("Room").document(f"Room {room_number}")

    doc_ref.set({
        "prompt_question": prompt_name,
        "prompt_description":prompt_description,
        "responses": all_response,
        "room_number": room_number,
        "num_participants": number_of_p,
        # "name_participants": p_name,
        "num_response":number_of_response, 
    })
