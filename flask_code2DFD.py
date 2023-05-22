from flask import Flask, jsonify, request

import code2DFD

app = Flask(__name__, instance_relative_config = True)

# Create default endpoint
@app.get('/')
def index():
    index_message = "API for DFD extraction. \
    Provide a GitHub URL to endpoint /dfd as parameter \"url\" to receive the extracted DFD: \
    /dfd?url=https://github.com/georgwittberger/apache-spring-boot \
           -microservice-example"

    return index_message


# Create endpoint /dfd
@app.get('/dfd')
def dfd():

    # Retrieve argument 'path' from request
    url = request.args.get("url")

    if not url:
        return "Please specify a URL, e.g. /dfd?url=https://github.com/georgwittberger/apache-spring-boot" \
               "-microservice-example "
    try:
        path = url.split("github.com/")[1]
    except:
        return "Please specify the complete URL, e.g. /dfd?url=https://github.com/georgwittberger/apache-spring-boot" \
               "-microservice-example "

    # Call Code2DFD
    results = code2DFD.api_invocation(path)

    # Create response JSON object and return it
    response = jsonify(
        codeable_models_file = results["codeable_models_file"],
        traceability_file = results["traceability"],
        execution_time = results["execution_time"]
    )

    return response


# starts local server
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
