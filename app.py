from flask import Flask, render_template, request, jsonify
import pandas as pd
import string
import re

app = Flask(__name__)

prev_input = []

# Load student data and query responses from Excel
student_data = pd.read_excel('student_data.xlsx')
query_response = pd.read_excel('Query_response.xlsx')
student_query = pd.read_excel('Student_Query.xlsx')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.form['user']

    # Define function to remove punctuation
    def remove_punctuation(text):
        return "".join([i for i in text if i not in string.punctuation])

    # Clean user input
    clean_user_input = remove_punctuation(user_input).lower()

    # Define function for tokenization
    def tokenization(text):
        return re.split(r'\W+', text)

    # Define function for checking if a string is an integer
    def is_integer(s):
        return s.isdigit() 

    # Tokenize and standardize "cgpa" and "contact" terms
    msg_tokenized = tokenization(clean_user_input)

    def lemmanize_cgpa(text):
        return "cgpa" if any(keyword in text for keyword in ["grade", "marks", "academic"]) else text

    def lemmanize_contact(text):
        return "contact" if any(keyword in text for keyword in ["mobile", "phone", "mob", "mobno"]) else text

    msg_tokenized = [lemmanize_cgpa(token) for token in msg_tokenized]
    msg_tokenized = [lemmanize_contact(token) for token in msg_tokenized]

    # Store previous inputs for context
    def store_input(text):
        if any(keyword in text for keyword in ["name", "roll", "cgpa", "contact", "year", "programme", "branch"]):
            prev_input.append(text)
        return text

    results = []

    for token in msg_tokenized:
        # Handle numeric inputs for student lookup
        if is_integer(token):
            to_int = int(token)
            student_info = student_data[student_data['PRNno'] == to_int].to_dict('records')
            if student_info:
                # Check for specific fields requested in previous input
                if "roll" in prev_input:
                    result_roll = {'success': True, 'roll': student_info[0]['RollNumber']}
                    prev_input.clear()
                    return jsonify(result_roll)
                if "cgpa" in prev_input:
                    result_cgpa = {'success': True, 'cgpa': student_info[0]['CGPA']}
                    prev_input.clear()
                    return jsonify(result_cgpa)
                if "contact" in prev_input:
                    result_contact = {'success': True, 'contact': student_info[0]['Contactnumber']}
                    prev_input.clear()
                    return jsonify(result_contact)
                if "year" in prev_input:
                    result_year = {'success': True, 'year': student_info[0]['Year']}
                    prev_input.clear()
                    return jsonify(result_year)
                if "programme" in prev_input:
                    result_programme = {'success': True, 'programme': student_info[0]['Programme']}
                    prev_input.clear()
                    return jsonify(result_programme)
                if "branch" in prev_input:
                    result_branch = {'success': True, 'branch': student_info[0]['Branch']}
                    prev_input.clear()
                    return jsonify(result_branch)
                if "name" in prev_input:
                    result_name = {'success': True, 'name': student_info[0]['StudentName']}
                    prev_input.clear()
                    return jsonify(result_name)
                else:
                    # Return all student data if no specific field was requested
                    result_student = {'success': True, 'data': student_info[0]}
                    return jsonify(result_student)
            else:
                results.append({'success': False, 'message': 'No student found'})
        else:
            token = store_input(token)

            # Check Student_Query for a match
            student_query_match = student_query[student_query['Query'].str.contains(token, case=False, na=False)].to_dict('records')
            if student_query_match:
                response_text = student_query_match[0].get("Response", "No response available")
                result_student_query = {'success': True, 'data': {'Response': response_text}}
                return jsonify(result_student_query)

            # Check Query_response for a general query match
            query_response_match = query_response[query_response['Query'].str.contains(token, case=False, na=False)].to_dict('records')
            if query_response_match:
                response_text = query_response_match[0].get("Response", "No response available")
                result_query_response = {'success': True, 'data': {'Response': response_text}}
                return jsonify(result_query_response)

            # If no match in both files, add "No response found"
            results.append({'success': False, 'message': 'No response found'})

    # Return results as JSON if no specific response was found
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
