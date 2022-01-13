
from re import L
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


# Add Rooms
def room_number_generator():
    return random.randint(1,1000)

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
                    st.write(f"### Your Response")
                    for i in range(number_of_response):
                        response_list[f'response {i}'] = st.text_input(f'Response {i+1}')
                    
                    all_response.append(response_list)
                    
                    submitted = st.form_submit_button("Submit")

            return all_response, submitted

        # if type(participant_data) == list:

        #     # create a dictionary to keep track of all the response
        #     all_response = []

        #     # Create a for loop to create all the response
        #     for respondant in range(len(participant_data)):
        #         with st.form(f"{participant_data[respondant]}"):
                    
        #             numberlist = [f'response {nr}' for nr in range(number_of_response)]
        #             response_list = dict.fromkeys(numberlist)
        #             st.write(f"### {participant_data[respondant]}")
        #             for i in range(number_of_response):
        #                 response_list[f'response {i}'] = st.text_input(f'Response {i+1}')
                    
        #             all_response.append(response_list)
                    
        #             st.form_submit_button("Submit")
                    
        #     return all_response


user_mode = st.selectbox('# Who are you?', ['Admin','Participant'])

if user_mode == "Admin":
    room_choice = st.radio('Open/Join Room', ["Open Room", "Join Room"])

    
    if room_choice == "Join Room":
        room_number = int(st.text_input('Room Number', value = 0))

    st.write("## ✋ The Prompt for Discussion")
    prompt_name = st.text_input('Prompt')
    prompt_description = st.text_input('Prompt description (optional)')
    number_of_response = st.slider(label ='Number of responses for each participant', min_value = 0, max_value = 20, value= 3) 

    finish = st.button("Create/Update a Room")

    if finish:
        if room_choice == 'Open Room':
            room_number = room_number_generator()
            
        doc_ref = db.collection("Room").document(f"Room {room_number}")
        doc_ref.set({
            "prompt_question": prompt_name,
            "prompt_description":prompt_description,
            "responses": [],
            "room_number": room_number,
            # "num_participants": number_of_p,
            # "name_participants": p_name,
            "num_response":number_of_response, 
        })
        st.write("\n")
        st.write(f"## 🔗 Your Room Number is {room_number}.")
        st.write("Invite people to your room")
        st.code(f"Join the discussion at [link](https://share.streamlit.io/cyrushhc/cyrushhc.github.io/main/myapp.py)\nEnter The room number: {room_number}.")
        

# st.write("## 👀 View Mode")
# mode = st.radio(label = "Choose a mode", options= ["Response","Result"])

elif user_mode == "Participant":
    
    # For some reasons I cannot use the stream() method 
    # It says that 'CollectionReference' object has no attribute 'stream'
    # room_ref = db.collection(u'Room')
    # room_id_list = []
    # st.write(room_ref.stream())
    # for rooms in room_ref.stream():
    #     room_id_list = [rooms.to_dict()['room_number']] 
    room_number = int(st.text_input('Room Number', value = 0))
    
    # if room_number != 0:
    try:
        doc_ref = db.collection("Room").document(f"Room {room_number}")
        doc = doc_ref.get()
        doc = doc.to_dict()
        prompt_name = doc['prompt_question'] 
        prompt_description = doc['prompt_description']

        st.write(f"### 🙃 Prompt: {prompt_name}")
        st.write(prompt_description)

        new_response, submitted = create_response(doc['num_response'], 1)

        # if create_participant == 'Enter Number of Participant':
        #     all_response = create_response(number_of_response, number_of_p)
            
        #     # create a form that will have a set number of response

        # elif create_participant == 'Enter Participant Name':
        #     p_name_list = p_name.split(",")
        #     all_response = create_response(number_of_response, p_name_list)

        if submitted:

            current_response = doc['responses']
            updated_response = current_response + new_response

            doc_ref.set({
                "prompt_question": doc['prompt_question'],
                "prompt_description":doc['prompt_description'],
                "responses": updated_response,
                "room_number": room_number,
                "num_response":doc['num_response'], 
            })

            st.write("Thank you for your input 👍")
        
    except:
        st.write("This room does not exist. Please enter a valid room number 🙏")