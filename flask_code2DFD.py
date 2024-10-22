from flask import Flask, jsonify, request

import code2DFD

app = Flask(__name__, instance_relative_config = True)


@app.get('/')
def index():
    index_message = ("API for DFD extraction. \
    Provide a GitHub URL to endpoint /dfd as parameter \"url\" to receive the extracted DFD: \
    /dfd?url=https://github.com/georgwittberger/apache-spring-boot \
           -microservice-example; \
                     Optionally provide a commit hash as \"commit\" parameter")

    return index_message


@app.get('/dfd')
def dfd():

    url = request.args.get("url")
    commit = request.args.get("commit", None)

    if not url:
        return "Please specify a URL, e.g. /dfd?url=https://github.com/georgwittberger/apache-spring-boot" \
               "-microservice-example "

    # Call Code2DFD
    results = code2DFD.api_invocation(url, commit)

    # Create response JSON object and return it
    response = jsonify(**results)

    return response


# starts local server
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)
