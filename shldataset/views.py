from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from shldjango.settings import MONGODB_URL,OPENAI_ACCESS_KEY
from pymongo.mongo_client import MongoClient
import openai
from django.http import JsonResponse
import pandas as pd
import json
from bson import json_util
def connect_to_db():
    try:
        client = MongoClient(MONGODB_URL)
        db = client["shl-datasetDB"]
        dataset_col = db["dataset"]
        return dataset_col
    except Exception as e:
        return "error"

def get_data(request):
    if request.method == 'GET':
        try:
            dataset = connect_to_db()
            if dataset == "error":
                data = {"success": False, "message": "something went wrong with DB connection!!"}
                return JsonResponse(data, status=500, safe=False)
            entries = list(dataset.find({},{"_id":0}))

            data = {"success": True, "data": entries}
            return JsonResponse(data, status=200, safe=False)
        except Exception as e:
            print(e)
            data = {"success": False, "message": "something went wrong try again!!"}
            return JsonResponse(data, status=500, safe=False)

@csrf_exempt
def get_serached_data(request):

    if request.method == 'POST':
        try:
            body_data = json.loads(request.body)
            phrase = body_data.get("text")

            dataset = connect_to_db()

            if dataset == "error":
                data = {"success": False, "message": "something went wrong with DB connection!!"}
                return JsonResponse(data, status=500, safe=False)

            heading_dict = {
                'title':'Title',
                'technologies':'Technologies',
                'frontend':'Frontend',
                'backend': 'Backend',
                'databases':'Databases',
                'infrastructure':'Infrastructre',
                'otherinformation': 'Availability'
            }

            result_list = get_from_gpt(phrase).replace(' ','').replace('-','').replace('\n','').lower().split(',')

            # if 'error' in result_list:
            #     data = {"success": False, "message": "something went wrong while using gpt!!"}
            #     return JsonResponse(data, status=500, safe=False)

            print(result_list)
            criteria = set()
            search_list = []
            for item in result_list:
                if item in heading_dict:
                    criteria.add(heading_dict[item])
                else:
                    search_list.append(item)

            if len(criteria) == 0:
                criteria.add('Availability')

            print(criteria,search_list)

            data = list(dataset.find({},{"_id":0}))

            searched_data = []
            already_existed_data = set()

            for index,obj in enumerate(data):
                for field in obj:
                    if field in criteria:
                        for str in search_list:
                             field_value = obj[field].replace(' ','').lower()
                             if field_value.find(str) != -1 and index not in already_existed_data:
                                 searched_data.append(obj)
                                 already_existed_data.add(index)


            data = {"success": True, "data": searched_data}
            return JsonResponse(data,status=200,safe=False)

        except Exception as e:
            print(e)
            data = {"success": False, "message": "something went wrong try again!!"}
            return JsonResponse(data, status=500, safe=False)


def get_from_gpt(phrase):

        openai.api_key = OPENAI_ACCESS_KEY

        user_query = "Extract the important keywords from the following phrase: " + phrase + ". Provide a list of significant terms or words."
        parsed_query = openai.Completion.create(
            model="text-davinci-002",
            prompt=user_query,
            max_tokens=200
        )

        parsed_data = parsed_query.choices[0].text.strip()
        return str(parsed_data)


def convertcsv(request):
    csv_file = '/home/birinder/practice/shl.xlsx'
    sheet = pd.read_excel(csv_file, sheet_name=0)

    data_list = []

    for index, row in sheet.iterrows():
        data_dict = dict()
        data_dict["Title"] = str(row["Project.Title"])
        if str(row["Technical_Skillset.Databases"]) == "nan":
            data_dict['Databases'] = ""
        else:
            data_dict["Databases"] = str(row["Technical_Skillset.Databases"])

        if str(row["Project.Technologies"]) == "nan":
            data_dict["Technologies"] = ""
        else:
            data_dict["Technologies"] = str(row["Project.Technologies"])

        if str(row["Technical_Skillset.Frontend"]) == "nan":
            data_dict["Frontend"] = ""
        else:
            data_dict["Frontend"] = str(row["Technical_Skillset.Frontend"])

        if str(row["Technical_Skillset.Backend"]) == "nan":
            data_dict["Backend"] = ""
        else:
            data_dict["Backend"] = str(row["Technical_Skillset.Backend"])

        if str(row["Technical_Skillset.Infrastructre"]) == "nan":
            data_dict["Infrastructre"] = ""
        else:
            # data_dict["Infrastructre"] = str(row["Technical_Skillset.Infrastructre"]).split(',')
            data_dict["Infrastructre"] = str(row["Technical_Skillset.Infrastructre"])

        data_dict["Availability"] = str(row["Other_Information.Availability"])
        data_list.append(data_dict)


    client = MongoClient(MONGODB_URL)
    db = client["shl-datasetDB"]
    dataset_col = db["dataset"]

    dataset_col.insert_many(data_list)
    #
    # # Convert DataFrame to a list of dictionaries (to_dict with 'records' argument)
    # data = df.to_dict(orient='records')
    #
    # # Insert data into MongoDB
    # dataset_col.insert_many(data)
