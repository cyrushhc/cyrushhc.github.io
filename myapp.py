
import streamlit as st
from google.cloud import firestore


# Authenticate to Firestore with the JSON account key.
db = firestore.Client.from_service_account_json("firestore-key.json")

# Create a reference to the Google post.
doc_ref = db.collection("Room").document("Room 1")

doc = doc_ref.get()

# Let's see what we got!
st.write("The id is: ", doc.id)
st.write("The contents are: ", doc.to_dict())

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
            number_list = [i for i in range (participant_data)]
            all_response = dict.fromkeys(number_list)
            

            # Create a for loop to create all the response
            for respondant in range(participant_data):

                with st.form(f"{respondant}"):
                    response_list = []
                    st.write(f"### Participant {respondant+1}")
                    for i in range(number_of_response):
                        response_list.append(st.text_input(f'Response {i+1}'))
                    
                    all_response[respondant]  = response_list
                    
                    st.form_submit_button("Submit")

            return all_response

        if type(participant_data) == list:

            # create a dictionary to keep track of all the response
            number_list = [i for i in range(len(participant_data))]
            all_response = dict.fromkeys(number_list)

            # Create a for loop to create all the response
            for respondant in range(len(participant_data)):

                with st.form(f"{participant_data[respondant]}"):
                    response_list = []
                    st.write(f"### {participant_data[respondant]}")
                    for i in range(number_of_response):
                        response_list.append(st.text_input(f'Response {i+1}'))
                    
                    all_response[respondant]  = response_list
                    
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
        
        # create a form that will have a set number of response with the participant name

    st.write(all_response)

finish = st.button("Done")


if finish:

    doc_ref = db.collection("Room").document("Room 2")

    doc_ref.set({
        "prompt_question": prompt_name,
        "prompt_description":prompt_description,
        # "response":all_response,
        "room_number": 2,
        "num_participants": number_of_p,
        # "name_participants": p_name,
        "num_response":number_of_response, 

    })



posts_ref = db.collection("Room")

for doc in posts_ref.stream():
    room = doc.to_dict()
    st.write(room)
    st.write("yo")
    