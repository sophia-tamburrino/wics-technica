#import ollama
import pandas as pd
import re

def main(path):
    #path will be a txt file.
    try:
        df = pd.read_csv(path)
        print(f"Loaded {len(df)} dialogues")
    except Exception as e:
        print(f"Failed to load txt: {e}")
        return None

    # # placeholder for classification results
    # classifications = []
    # explanations = [] # separated from classifications so its easier to parse through later on

    # # loop through each dialogue-response pair
    # for index, row in df.iterrows():
    #     dialogue = row.get('Dialogue', '')

    #     # editing to get llama to generate a response
    #     # generate prompt for specific dialogue-response pair
    #     prompt = f"""
    #     Generate a question based on a student's uploaded notes. 
        
    #     Your Task:
        
    #     Now it is your turn to create banter. Given Part A below, your task is to immediately provide a suitable Part B.
    #     - Part A: "{dialogue}"
    #     - Part B:
        
    #     IMPORTANT: Your response must start with "Part B: " followed by your suitable Part B.
    #     """
    #     try:
    #         # generate response from llama
    #         model_response = ollama.generate(model='llama3.2', prompt=prompt)
    #         raw_response = model_response.get('response', '').strip()

    #         # extract classification using regex
    #         match = re.search(r'Part B:', raw_response)
    #         if match:
    #             # classification = int(match.group(1))
    #             # classifications.append(classification)

    #             # extract explanation
    #             explanation_start = raw_response.find(match.group(0)) + len(match.group(0))
    #             explanation = raw_response[explanation_start:].strip()
    #             explanations.append(explanation)

    #             # print both classification and explanation
    #             print(f"Part A: {dialogue}")
    #             print(f"Part B: {explanation}")

    #             write_output(df, index, explanation)
                
    #         else:
    #             raise ValueError(f"Unexpected response format: {raw_response}")
            
    #         #ERRORS GENERATE ON LINES 148, 648, 946
            
    #     except Exception as e:
    #         print(f"Error generating question {index}: {e}")
    #         classifications.append(None)  # mark error cases
    #         explanations.append(None)

main('/os-notes') #add path, the user-provided CSV
