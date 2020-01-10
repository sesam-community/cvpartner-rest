from flask import Flask, request, Response, abort, jsonify
import os
import requests
import logging
import json
import dotdictify
from time import sleep
import base64
import cherrypy


app = Flask(__name__)

os.environ['base_url'] = "https://bouvet.cvpartner.com/api/"
os.environ['custom_tag_category_url'] = "v1/masterdata/custom_tags/custom_tag_category"
os.environ["custom_tag_url"] = "v1/masterdata/custom_tags/custom_tag"
os.environ["delete_company_images"] = "True"
os.environ["entities_path"] = "values"
os.environ["headers"] = "{'Accept':'application/json', 'Content-Type':'application/json', 'Authorization':'Token 33db24341aa7f3ad22c8242aaf8005d8'}"
os.environ["log_level"]= "DEBUG"
os.environ["next_page"]= "next.href"
os.environ["reference_url"]= "v3/references/search?size=1000&from=0"
os.environ["references_path"]= "references"
os.environ["set_id"]= "cvpartner:set_id"
os.environ["sleep"]= "0.400"
os.environ["token"]= "Token 33db24341aa7f3ad22c8242aaf8005d8"
os.environ["user_url"]= "v1/users"

headers = {}
if os.environ.get('headers') is not None:
    headers = json.loads(os.environ.get('headers').replace("'", "\""))

@app.route("/cv", methods=["GET"])
def get_cv():
    path = os.environ.get("user_url")
    url = os.environ.get("base_url") + path
    req = requests.get(url, headers=headers)
    print('------------------------------------')
    print(req)
    print('------------------------------------')
    if req.status_code != 200:
        print("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
        raise AssertionError("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
    clean = json.loads(req.text)
    print(clean[:5])
    cv_url = os.environ.get("base_url") + "v3/cvs/"
    return jsonify(clean)


if __name__ == '__main__':

    # This is used when running locally. Gunicorn is used to run the
    # application on Google App Engine. See entrypoint in app.yaml.
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
