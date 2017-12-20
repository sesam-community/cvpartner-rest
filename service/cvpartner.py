from flask import Flask, request, Response
import os
import requests
import logging
import json
import dotdictify
from time import sleep
import base64


app = Flask(__name__)
logger = None
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger('cvpartner-rest-service')

# Log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(logging.Formatter(format_string))
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

headers = {}
if os.environ.get('headers') is not None:
    headers = json.loads(os.environ.get('headers').replace("'","\""))

def encode(v):
    for key, value in v.items():
        if isinstance(value,dict):
            encode(value)
        else:
            v[key] = base64.b64encode(requests.get(value).content).decode("utf-8")

    return v

def transform(obj):
    res = {}
    # print(obj.items())
    for k, v in obj.items():
        if k == "image":
            if dotdictify.dotdictify(v).large.url is not None:
                logger.info("Encoding images from url to base64...")
                res[k] = encode(v)

            else:
                pass
        try:
            _ = json.dumps(v)
        except Exception:
            pass
        else:
            res[k] = v
    return res

class DataAccess:

    def __get_all_users(self, path):
        logger.info("Fetching data from url: %s", path)
        url=os.environ.get("base_url") + path
        req = requests.get(url, headers=headers)

        if req.status_code != 200:
            logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
            raise AssertionError("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
        clean = json.loads(req.text)
        for entity in clean:
            yield transform(entity)

    def __get_all_cvs(self, path):
        logger.info("Fetching data from url: %s", path)
        url=os.environ.get("base_url") + path
        req = requests.get(url, headers=headers)

        if req.status_code != 200:
            logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
            raise AssertionError("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
        clean = json.loads(req.text)
        cv_url = os.environ.get("base_url") + "v3/cvs/"
        for entity in clean:
            for k, v in entity.items():
                if k == "id":
                    cv_url += v + "/"
            for k, v in entity.items():
                if k == "default_cv_id":
                    cv_url += v
            req = requests.get(cv_url, headers=headers)
            if req.status_code != 200:
                logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
                raise AssertionError(
                    "Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
            cv = json.loads(req.text)
            yield transform(cv)
            cv_url = os.environ.get("base_url") + "v3/cvs/"

    def __get_all_paged_entities(self, path):
        logger.info("Fetching data from paged url: %s", path)
        url = os.environ.get("base_url") + path
        next_page = url
        page_counter = 1
        while next_page is not None:
            if os.environ.get('sleep') is not None:
                logger.info("sleeping for %s milliseconds", os.environ.get('sleep') )
                sleep(float(os.environ.get('sleep')))

            logger.info("Fetching data from url: %s", next_page)
            req = requests.get(next_page, headers=headers)
            if req.status_code != 200:
                logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
                raise AssertionError ("Unexpected response status code: %d with response text %s"%(req.status_code, req.text))
            dict = dotdictify.dotdictify(json.loads(req.text))
            yield transform(dict)

            dict.get(os.environ.get("entities_path"))
            if dict.get(os.environ.get('next_page')) is not None:
                page_counter+=1
                next_page = dict.get(os.environ.get('next_page'))
            else:
                next_page = None
        logger.info('Returning entities from %i pages', page_counter)


    def get_paged_entities(self,path):
        print("getting all paged")
        return self.__get_all_paged_entities(path)

    def get_users(self, path):
        print('getting all users')
        return self.__get_all_users(path)

    def get_cvs(self, path):
        print('getting all cvs')
        return self.__get_all_cvs(path)

data_access_layer = DataAccess()


def stream_json(clean):
    first = True
    yield '['
    for i, row in enumerate(clean):
        if not first:
            yield ','
        else:
            first = False
        yield json.dumps(row)
    yield ']'

@app.route("/<path:path>", methods=["GET"])
def get(path):
    entities = data_access_layer.get_paged_entities(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )

@app.route("/user", methods=["GET"])
def get_user():
    path = os.environ.get("user_url")
    entities = data_access_layer.get_users(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )

@app.route("/cv", methods=["GET"])
def get_cv():
    path = os.environ.get("user_url")
    #path = "v1/users?" + "limit=" + os.environ.get("limit")
    entities = data_access_layer.get_cvs(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('port',5000))
