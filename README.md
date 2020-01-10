# CVpartner REST service
[![Build Status](https://travis-ci.org/sesam-community/cvpartner-rest.svg?branch=master)](https://travis-ci.org/sesam-community/cvpartner-rest)

A small microservice to get entities from a REST api.

This microservice needs information about path to the url of the next page (more in example config).

##### Environment variables
```
"base_url": The common, first part of the url to the REST-api. The other url variables are appended to base_url for use at runtime.
"custom_tag_category_url": Path for GET of custom tag categories containing their custom tags.
"custom_tag_url": Path for POST and PUT of custom tags.
"delete_company_images": We don't want generic images in Sesam, this removes them on the way in if "True". Defaults to "False".
"entities_path": In which property your entities reside in the result from GET.
"headers": The headers to send with your HTTP-request.
"log_level": Set the level of logging messages to output. Defaults to "INFO".
"next_page": Path in returned paged-entity object to href of next page.
"reference_post": Data to send with POST to reference_url
"reference_url": Path for GET of references.
"references_path": Path to references in return object from reference_url
"sleep_increment": Incremental time (s) the MS sleeps for each 429 response. The total sleep time adds up until it reached 'sleep_max'.
"sleep_max": The maximum number of seconds the MS can sleep
"sleep":  Miliseconds to sleep between each rest call.
"user_url": Path to users in REST-api. Supports POST, PUT and GET.
```

##### RETURNED example paged-entity
```
[
    {
        "id":"2",
        "foo": "bar"
    },
    {
        "id":"3",
        "foo": "baz"
    }
]
```

##### GET example pipe config
```
[
    "_id": "cvpartner-users",
    "type": "pipe",
    "source": {
        "type": "json",
        "system": "cvpartner",
        "url": "/user"
    }
]
```


##### Example result from GET method with paged entity
```
{
  "href": "http://foo.com/api/v1/users",
    "values": [
    {
      "id": "1",
      "cv_id": "2",
      "name": "Ashkan",
      "custom_tags": [
        "595a082e77fe09263b7fea20",
        "5954f44d3a4e6107feaea292",
        "5954f4a159264807599b31c2"
      ],
      "skills": [
        "58f756f4502bdb084adaddb4",
        "58f7785b502bdb07f8dade23",
        "594447d938cf5f0ab3315a98",
        "59aea857aca9200810994931"
      ],
      "customers": [
        "5825b3072c04d6206f27f005"
      ],
      "industries": []
    }
  ],
  "total": 2262,
  "next": {
    "href": "http://foo.com/api/v1/users?limit=100&offset=100"
  }
}
```
This will result into returned entities:
```
[
    {
      "id": "1",
      "cv_id": "2",
      "name": "Ashkan",
      "custom_tags": [
        "595a082e77fe09263b7fea20",
        "5954f44d3a4e6107feaea292",
        "5954f4a159264807599b31c2"
      ],
      "skills": [
        "58f756f4502bdb084adaddb4",
        "58f7785b502bdb07f8dade23",
        "594447d938cf5f0ab3315a98",
        "59aea857aca9200810994931"
      ],
      "customers": [
        "5825b3072c04d6206f27f005"
      ],
      "industries": []
    }
]
```

##### Example POST/PUT pipe config
```
{
  "_id": "department-cvpartner-endpoint",
  "type": "pipe",
  "source": {
    "type": "dataset",
    "dataset": "department-cvpartner"
  },
  "sink": {
    "type": "json",
    "system": "cv-partner-rest",
    "url": "/custom_tag"
  }
}
```

##### Example POST/PUT entities

POST custom tag
```
{
  "_id": "ad-department:500",
  "department-cvpartner:operation": "post",
  "department-cvpartner:payload": {
    "masterdata": {
      "category_ids": [
        "586cf0be285db12d00d9e1e5"
      ],
      "external_unique_id": "500",
      "values": {
        "no": "Alle Sesam"
      }
    }
  }
}
```

PUT custom tag
```
{
  "_id": "ad-department:753",
  "department-cvpartner:id": "5d4aa9043330eb0e7cd32d1e",
  "department-cvpartner:operation": "put",
  "department-cvpartner:payload": {
    "masterdata": {
      "custom_tag_category_id": "586cf0be285db12d00d9e1e5",
      "external_unique_id": "753",
      "values": {
        "no": "Stavanger Tech 1"
      }
    }
  }
}
```

POST user
```
{
  "_id": "ad-user:0006",
  "user-cvpartner:operation": "post",
  "user-cvpartner:payload": {
    "user": {
      "country_id": "586cee3f2c04d65514314910",
      "email": "abc@bouvet.no",
      "ensure_unique_custom_tag_ids_by_category": {
      },
      "external_unique_id": "0006",
      "name": "Testina Testsen",
      "office_id": "5d4be151edfc710ffab8330c",
      "role": "Consultant",
      "telephone": "+47 66666666"
    }
  }
}
```

PUT user
```
{
  "_id": "ad-user:0001",
  "user-cvpartner:id": "5d4d3352b3a1750e59112486",
  "user-cvpartner:operation": "put",
  "user-cvpartner:payload": {
    "country_id": "586cee3f2c04d65514314910",
    "ensure_unique_custom_tag_ids_by_category": {
    },
    "external_unique_id": "0001",
    "office_id": "5d4be141b3a1750e59111ff3",
    "upn": "kari.norrman@bouvet.no"
  }
}
```
##### Example configuration:

```
{
  "_id": "cvpartner",
  "type": "system:microservice",
  "docker": {
    "environment": {
      "base_url": "https://some-rest-service.com/api/",
      "cvpartner-custom-tag-category-url": "v1/masterdata/custom_tags/custom_tag_category",
      "cvpartner-custom-tag-url": "v1/masterdata/custom_tags/custom_tag",
      "delete_company_images": "True",
      "entities_path": "values",
      "headers": "{'Accept':'application/json', 'Content-Type':'application/json', 'Authorization':'$SECRET(token)'}",
      "next_page": "next.href",
      "sleep_increment": 0.5,
      "sleep_max": 20,
      "user_url": "v1/user",
    },
    "image": "sesamcommunity/cvpartner-rest:latest",
    "port": 5000
  }
}
```

