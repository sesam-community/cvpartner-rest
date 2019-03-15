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

def str_to_bool(string_input):
    return str(string_input).lower() == "true"

def transform(obj):
    res = {}
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
            yield entity

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
            if str_to_bool(os.environ.get('delete_company_images', "False")) == True:
                for i in range(len(cv["project_experiences"])):
                    del cv["project_experiences"][i]["images"]
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
            for entity in dict.get(os.environ.get("entities_path")):
                yield transform(entity)

            if dict.get(os.environ.get('next_page')) is not None:
                page_counter+=1
                next_page = dict.get(os.environ.get('next_page'))
            else:
                next_page = None
        logger.info('Returning entities from %i pages', page_counter)

    def __get_all_references(self, path):
        logger.info('Fetching data from paged url: %s', path)
        url = os.environ.get("base_url") + path
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Token 4d46ab8e5dddb0fd1fcb93567ea94482"
        }
        post_data = {
            "offset": 0,
            "size": 10,
            "must": [
                {
                    "bool": {
                        "should": [
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "5761326569702d4e41000000"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "580e3e9a2c04d627b6210c52"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "5085b1c5a6add17a1500000e"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "5761332f69702d4fa9000000"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "576120ce69702d333e000000"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "576120a469702d32db000000"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "5837ee3d2c04d618a4d70891"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "5837ee672c04d618f47a2988"
                                }
                            },
                            {
                                "exact": {
                                    "field": "office_id",
                                    "value": "5761224069702d3754000000"
                                }
                            },
                            {
                                "not_exist": "office_id"
                            }
                        ]
                    }
                }
            ]
        }
        total_amount = json.loads(requests.post(url, data=json.dumps(post_data), headers=headers).text)["total"]
        counter = 0
        size = 10
        while counter < total_amount:
            logger.info(post_data)
            req = requests.post(url, data=json.dumps(post_data), headers=headers)
            res = dotdictify.dotdictify(json.loads(req.text))
            counter += size
            post_data["offset"] = counter
            entities = res.get(os.environ.get("references_path"))
            for entity in entities:
                yield(entity)

    def get_paged_entities(self,path):
        print("getting all paged")
        return self.__get_all_paged_entities(path)

    def get_users(self, path):
        print('getting all users')
        return self.__get_all_users(path)

    def get_cvs(self, path):
        print('getting all cvs')
        return self.__get_all_cvs(path)

    def get_references(self, path):
        print('getting all references')
        return self.__get_all_references(path)

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

@app.route("/<path:path>", methods=["GET", "POST"])
def get(path):
    entities = data_access_layer.get_paged_entities(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )

@app.route("/references", methods=["GET"])
def get_references():
    path = os.environ.get("reference_url")
    entities = data_access_layer.get_references(path)
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
    entities = data_access_layer.get_cvs(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', threaded=True, port=os.environ.get('port',5000))
