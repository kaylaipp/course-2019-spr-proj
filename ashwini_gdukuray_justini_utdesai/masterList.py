import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
import pandas as pd


class masterList(dml.Algorithm):
    contributor = 'ashwini_gdukuray_justini_utdesai'
    reads = ['ashwini_gdukuray_justini_utdesai.massHousing', 'ashwini_gdukuray_justini_utdesai.secretary', 'ashwini_gdukuray_justini_utdesai.validZipCodes'] # is going to have to read in the master list from mongodb
    writes = ['ashwini_gdukuray_justini_utdesai.masterList'] # will write a dataset that is companies in top 25 that are also certified MBE

    @staticmethod
    def execute(trial=False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('ashwini_gdukuray_justini_utdesai', 'ashwini_gdukuray_justini_utdesai')

        # Need to standardize the columns and field structure of massHousing and secretary and union the two
        # in order to create a master MBE list, and then store it in the DB

        massHousing = repo['ashwini_gdukuray_justini_utdesai.massHousing']
        secretary = repo['ashwini_gdukuray_justini_utdesai.secretary']
        validZips = repo['ashwini_gdukuray_justini_utdesai.validZipCodes']

        massHousingDF = pd.DataFrame(list(massHousing.find()))
        secretaryDF = pd.DataFrame(list(secretary.find()))
        validZipsDF = pd.DataFrame(list(validZips.find()))

        #print(list(secretaryDF))
        #print(list(massHousingDF))

        # clean up secretary dataset
        # convert zip codes to strings and 5 digits long
        secretaryDF['Zip'] = secretaryDF['Zip'].astype('str')
        secretaryDF['Zip'] = secretaryDF['Zip'].apply(lambda zipCode: ((5 - len(zipCode))*'0' + zipCode \
                                                        if len(zipCode) < 5 else zipCode)[:5])
        secretaryDF = secretaryDF.loc[secretaryDF['MBE - Y/N'] == 'Y']
        secretaryDF = secretaryDF[['Business Name', 'Address', 'City', 'Zip', 'State', 'Description of Services']]


        # clean up massHousing dataset
        massHousingDF['Zip'] = massHousingDF['Zip'].apply(lambda zipCode: zipCode[:5])
        massHousingDF = massHousingDF[['Business Name', 'Address', 'City', 'Zip', 'State', 'Primary Trade', 'Primary Other/Consulting Description']]

        for index, row in massHousingDF.iterrows():
            if (row['Primary Trade'] == 'Other: Specify'):
                row['Primary Trade'] = row['Primary Other/Consulting Description']

        massHousingDF = massHousingDF.rename(index=str, columns={'Primary Trade': 'Description of Services'})
        massHousingDF = massHousingDF.drop(columns=['Primary Other/Consulting Description'])


        # merge and create masterList
        preMasterList = pd.merge(massHousingDF, secretaryDF, how='outer', on=['Business Name', 'City', 'Zip'])

        preDict = {'Business Name': [], 'Address': [], 'City': [], 'Zip': [], 'State': [], 'Description of Services': []}

        for index, row in preMasterList.iterrows():

            desc = row['Description of Services_x']

            preDict['Business Name'].append(row['Business Name'])
            preDict['City'].append(row['City'])
            preDict['Zip'].append(row['Zip'])

            if pd.isnull(desc):
                preDict['State'].append(row['State_y'])
                preDict['Address'].append(row['Address_y'])
                preDict['Description of Services'].append(row['Description of Services_y'])
            else:
                preDict['State'].append(row['State_x'])
                preDict['Address'].append(row['Address_x'])
                preDict['Description of Services'].append(row['Description of Services_x'])


        masterList = pd.DataFrame(preDict)

        # filter out invalid zips
        validZipsDF['Zip'] = validZipsDF['Zip'].astype('str')
        validZipsDF['Zip'] = validZipsDF['Zip'].apply(lambda zipCode: ((5 - len(zipCode))*'0' + zipCode \
                                                        if len(zipCode) < 5 else zipCode)[:5])
        listOfGoodZips = validZipsDF['Zip'].tolist()

        masterList = masterList[masterList['Zip'].isin(listOfGoodZips)]

        records = json.loads(masterList.T.to_json()).values()

        print(masterList)

        repo.dropCollection('masterList')
        repo.createCollection('masterList')
        repo['ashwini_gdukuray_justini_utdesai.masterList'].insert_many(records)
        repo['ashwini_gdukuray_justini_utdesai.masterList'].metadata({'complete': True})
        print(repo['ashwini_gdukuray_justini_utdesai.masterList'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}

    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        pass
        """
        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('alice_bob', 'alice_bob')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('bdp', 'https://data.cityofboston.gov/resource/')

        this_script = doc.agent('alg:alice_bob#example',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'], 'ont:Extension': 'py'})
        resource = doc.entity('bdp:wc8w-nujj',
                              {'prov:label': '311, Service Requests', prov.model.PROV_TYPE: 'ont:DataResource',
                               'ont:Extension': 'json'})
        get_found = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        get_lost = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_found, this_script)
        doc.wasAssociatedWith(get_lost, this_script)
        doc.usage(get_found, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=Animal+Found&$select=type,latitude,longitude,OPEN_DT'
                   }
                  )
        doc.usage(get_lost, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval',
                   'ont:Query': '?type=Animal+Lost&$select=type,latitude,longitude,OPEN_DT'
                   }
                  )

        lost = doc.entity('dat:alice_bob#lost',
                          {prov.model.PROV_LABEL: 'Animals Lost', prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(lost, this_script)
        doc.wasGeneratedBy(lost, get_lost, endTime)
        doc.wasDerivedFrom(lost, resource, get_lost, get_lost, get_lost)

        found = doc.entity('dat:alice_bob#found',
                           {prov.model.PROV_LABEL: 'Animals Found', prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(found, this_script)
        doc.wasGeneratedBy(found, get_found, endTime)
        doc.wasDerivedFrom(found, resource, get_found, get_found, get_found)

        repo.logout()

        return doc
        """


'''
# This is example code you might use for debugging this module.
# Please remove all top-level function calls before submitting.
example.execute()
doc = example.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))
'''

## eof
