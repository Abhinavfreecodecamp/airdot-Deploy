import redis
import json
from airdot.helpers.general_helpers import get_datetime

class redis_helper:
    def __init__(self, host, port, db=None):
        self.host = host
        self.port = port
        self.db = db
        self.redis = redis.Redis(host=self.host, port=self.port, db=self.db)
    
    def set_key(self, key, value):
        self.redis.set(key, value)
    
    def get_key(self, key):
        return self.redis.get(key)
    
    def delete_key(self, key):
        self.redis.delete(key)
    
    def get_keys(self, pattern):
        return self.redis.keys(pattern)
    
    def increment_key(self, key):
        self.redis.incr(key)
    
    def decrement_key(self, key):
        self.redis.decr(key)

    def set_user_function(self, id, deploy_dict, function_curl_req, object_refresh=False):
        user_function = self.get_key(id)
        if user_function is not None: # for a old deployment 
            user_function = json.loads(user_function)
            user_function[deploy_dict['name']]['curl'] = function_curl_req
            user_function[deploy_dict['name']]['version'] = user_function[deploy_dict['name']]["version"] + 1 if not(object_refresh) else user_function[deploy_dict['name']]["version"]
            user_function[deploy_dict['name']]['dataFiles'][get_datetime()] = '' if deploy_dict['dataFiles'] is None else deploy_dict['dataFiles'] 
            user_function[deploy_dict['name']]['metadata'] = {
                    "pythonVersion":deploy_dict['pythonVersion']  if not(object_refresh) else user_function[deploy_dict['name']]['metadata']['pythonVersion'],
                    "argTypes":deploy_dict['argTypes'] if not(object_refresh) else user_function[deploy_dict['name']]['metadata']['argTypes'],
                    "argNames":deploy_dict['argNames'] if not(object_refresh) else user_function[deploy_dict['name']]['metadata']['argNames']
            }
        else:
            user_function = dict()
            user_function[deploy_dict['name']] = {
                "curl": function_curl_req,
                "version": 1,
                "dataFiles": {get_datetime(): '' if deploy_dict['dataFiles'] is None else deploy_dict['dataFiles']},
                "metadata" : {
                    "pythonVersion":deploy_dict['pythonVersion'],
                    "argTypes":deploy_dict['argTypes'],
                    "argNames":deploy_dict['argNames']
                }
            }
        try:
            status = self.set_key(id, json.dumps(user_function),)
            return status
        except Exception as e:
            return None
    
