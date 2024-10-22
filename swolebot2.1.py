from openai import OpenAI
client = OpenAI()

import weaviate
import weaviate.classes as wvc
from weaviate.classes.query import Filter
import os
import json
import preload_database

def get_msg_completion(client: OpenAI, messages, temperature: float = 0, model: str = 'gpt-3.5-turbo') -> str:
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content

chatbot_context = [
    {
        "role": "system",
        "content": """You are SwoleBot, an automated service to create personalized workout plans. You will talk in an enthusiastic and encouraging "macho, gym-bro" voice.
    Rule 1 - You must always follow this rule. Do not answer any questions that are not asked in the prompt. If the user asks a question that is not in the prompt, you should respond with "I'm sorry, I can't help with that. Please stick to the questions asked."
    Rule 2 - Get answers to all 3 questions before generating a workout plan. If the user does not answer a question, ask it again. If the user answers a question with something other than the options provided, ask the question again.
    Rule 3 - If the user submits nothing, which is the empty string "", end the conversation will end. Do not output anything else.

    Step 1 - Inquire about the muscle group/groups they want an exercise for: "Which muscle group/groups do you want your exercise to work?"
    Step 2 - If the user's response is not a muscle group, like biceps, triceps, chest, back, legs, or shoulders, or core go back to Step 1.
    Step 3 - Explore the user's preferences and constraints: "Do you want to lift in the gym or at home?"
    Step 4 - If the user's response is not one of the two options, go back to Step 3.
    Step 5 - Ask the user if how difficult the maximum difficulty the exercise should be on a scale of 1 to 5. "How difficult do you want the exercise to be? 1 being the easiest and 5 being the hardest."
    Step 6 - If the user's response is not the number 1, 2, 3, 4, or 5, go back to Step 5.
    Step 7 - Ask how many exercises the user would like to get from the database: "How many exercises would you like to get from the database?"
    Step 8 - If the user's response is not an number between 1 and 10, say "Number invalid" and go back to step 7.
    Step 9 - Restate the user's choices and ask for confirmation: "Just to confirm, you want to work the [muscle group/groups] looking to lift at [user's exercise location] and you want the exercise to be a [user's lifting difficulty] out of 5. You would like to see [number of exercises]. Is that correct?"
    Step 10 - If the user does not confirm, update their fitness level, exercise location, and lifting frequency with what they would like to change and go back to Step 1. Do not move on before going back to step 1.
    Step 11 - If the user confirms their choices, return a summary of their query. "Great! You want to work the [muscle group/groups] looking to lift at [user's exercise location] and you want the exercise to be a [user's lifting difficulty] out of 5. I will search for [number of exercises] exercises. Querying database now". You MUST say this quote verbatim, it is very important to output this exact quote. The database will be queried in a separate function, you may assume that by the time you go to the next step, the exercise information will be available to you. Do not make up your own exercises.
    Step 12 - Ask the user if they have any changes they would like to make. If the user has changes to make, return to step 1. Do not move on before going back to step 1.
    Step 13 - If the user has no changes, confirm the finalized workout plan with the user: "Great! Your exercise has been selected! Let me know if you need another exercise!"
    Step 14 - If the user wants another exercise, return to step 1. Do not move on before going back to step 1.
    Step 15 - If not, thank the user for using SwoleBot and offer assistance for any future inquiries: "Thank you for creating your workout plan with me! Feel free to reach out anytime if you need further assistance or support. Have a fantastic workout!"
    """
    }
]

def collect_messages(client: OpenAI, exercise_info) -> str:
    prompt = input("User> ")
    chatbot_context.append({"role": "user", "content": prompt})
    input_to_flag = client.moderations.create(input=chatbot_context[-1]["content"])
    flagged = input_to_flag.results[0].flagged
    
    if flagged:
        print("Assistant> This response was flagged as inappropriate. Please try again.")
    else:
        response = get_msg_completion(client, chatbot_context)
        input_to_flag = client.moderations.create(input=response)
        flagged = input_to_flag.results[0].flagged

        if flagged:
            print("AI response was flagged as inappropriate. Continuing.")
        else:
            if "Querying database now" in response:

                how_hard = int(response.split("exercise to be a ")[1].split(" out of")[0])

                number_to_get = int(response.split("I will search for ")[1].split(" exercises.")[0])

                response = response.split(" I will search for")[0]
                
               
                data_response = exercise_info.query.near_text(query=response, filters=Filter.by_property("difficulty").less_or_equal(how_hard), limit=number_to_get)

                
                # Prepare the response from the database
                exercise_list = [f"{obj.properties['name']}, \ndifficulty: {obj.properties['difficulty']} \nHow to perform:\n{obj.properties['description']}\n" for obj in data_response.objects]
                exercise_string = "\n".join(exercise_list)

                complete_exercise_list = [f"{obj.properties['name']}, \nbody part: {obj.properties['body_part']}, \nmuscle group: {obj.properties['muscle_group']}, \ndifficulty: {obj.properties['difficulty']} \nAt home: {obj.properties['at_home']} \nHow to perform:\n{obj.properties['description']}\n" for obj in data_response.objects]
                complete_exercise_list = "\n".join(complete_exercise_list)

                db_response = f"The top {number_to_get} exercises that follow your criteria are:\n{exercise_string}."

                completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a robot that will determine how well a question is answered by a specific answer, and how much so, by outputting a number between 0 and 1. The closer to 1, the better the answer answers the question."}, 
                          {"role": "user", "content": f"""If the query is {response}, is {complete_exercise_list} a proper answer? You should answer based on how close the answer is to the query.
                           The main thing to focus on is if the workout works the muscle group/groups. Things like if the difficulty level is correct and if the exercise is at home or in the gym is not as important. Only respond with a number between 0 and 1."""}])
                
                relevancy = float(completion.choices[0].message.content)
                print(f"Relevancy: {relevancy}")
                if relevancy < 0.5:
                    db_response = "I'm sorry, I can't help with that. Please stick to the questions asked."
                    print("Assistant> I'm sorry, the database couldn't get a relevant answer.")
                else:



                    chatbot_context.append({"role": "assistant", "content": complete_exercise_list})
                
                    print(f"Assistant> {db_response}")
            else:
                print(f"Assistant> {response}")
                chatbot_context.append({"role": "assistant", "content": response})
                return prompt

def main():
    client = OpenAI()
    data_client, collection = preload_database.make_everything("bodybuilding_collection")
    exercise_info = data_client.collections.get("bodybuilding_collection")

    print("Welcome to SwoleBot, an automated service to supply specific exercises for you.")
    prompt = collect_messages(client, exercise_info)
    
    while prompt != "":
        prompt = collect_messages(client, exercise_info)
    print("Goodbye!")

if __name__ == "__main__":
    main()


