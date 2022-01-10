import streamlit as st
#from sentence_transformers import SentenceTransformer, util
#model = SentenceTransformer('stsb-roberta-large')

# Change the size of the sidebar
st.markdown(f'''
    <style>
        section[data-testid="stSidebar"] .css-ng1t4o {{width: 30vw;}}
        section[data-testid="stSidebar"] .css-1d391kg {{width: 30vw;}}
        section[data-testid="stSidebar"] .css-ng1t4o {{padding-right: 7%; padding-left:7%;}}
        section[data-testid="stSidebar"] .css-1d391kg {{padding-right: 7%; padding-left:7%;}}
    </style>
''', unsafe_allow_html=True)


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

# Creaet a prompt that would ask users to input the prompt 
# and how mant responses they want 

# with st.sidebar.form("prompt"):
    
#     # Every form must have a submit button.
#     submitted = st.form_submit_button("Submit")


st.sidebar.write("## The Prompt for Discussion")
prompt_name = st.sidebar.text_input('Prompt')
prompt_description = st.sidebar.text_input('Prompt description (optional)')
# Let users choose whether they want to create based on name or number of participant

create_participant = st.sidebar.radio('how would you like to create parcipant for this prompt?', ['Enter Participant Name', 'Enter Number of Participant'])

if create_participant == "Enter Participant Name":
    p_name = st.sidebar.text_input("Enter Partcipant Name (separated by comma ',' )")
elif create_participant == 'Enter Number of Participant':
    number_of_p = st.sidebar.slider("Number of Participant",max_value = 20) 


number_of_response = st.sidebar.slider(label ='Number of responses for each participant', min_value = 0, max_value = 20) 


st.write(f"### 🙃 Prompt: {prompt_name}")
st.write(prompt_description)

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

            # split them into 2 columns


            with st.form(f"{respondant}"):
                response_list = []
                st.write(f"### Participant {respondant+1}")
                for i in range(number_of_response):
                    response_list.append(st.text_input(f'Response {i+1}'))
                
                all_response[respondant]  = response_list
                
                st.form_submit_button("Submit")

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



if create_participant == 'Enter Number of Participant':
    create_response(number_of_response, number_of_p)
    
    # create a form that will have a set number of response

elif create_participant == 'Enter Participant Name':
    p_name_list = p_name.split(",")
    create_response(number_of_response, p_name_list)
    
    # create a form that will have a set number of response with the participant name










