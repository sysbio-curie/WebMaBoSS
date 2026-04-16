from rest_framework.views import APIView
from rest_framework.response import Response

import requests

class BioModelsAPI(APIView):

    def __init__(self, *args, **kwargs):
        APIView.__init__(self, *args, **kwargs)
    
    def get(self, request):
        
        response = requests.get('https://www.biomodels.org/search?query=modellingapproach%3A%22logical%20model%22&numResults=100&format=json', headers={'accept': '*/*'}).json()
        # count = response["matches"]
        models = response["models"]
        return Response([{'id' : model["id"], 'name': model["name"], 'author': model["submitter"]} for model in models])
