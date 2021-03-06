import urllib.request
import json
import dml
import prov.model
import datetime
import uuid


class linkedin(dml.Algorithm):
    contributor = 'ojhamb_runtongy_sgullett_zybu'
    reads = []
    writes = ['ojhamb_runtongy_sgullett_zybu.linkedin']

    @staticmethod
    def execute(trial=False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('ojhamb_runtongy_sgullett_zybu', 'ojhamb_runtongy_sgullett_zybu')

        url = 'http://datamechanics.io/data/link_am.json'
        response = urllib.request.urlopen(url).read().decode("utf-8")
        if trial:
            r = json.loads(response)[:30]
        else:
            r = json.loads(response)

        repo.dropCollection("linkedin")
        repo.createCollection("linkedin")
        repo['ojhamb_runtongy_sgullett_zybu.linkedin'].insert_many(r)
        repo['ojhamb_runtongy_sgullett_zybu.linkedin'].metadata({'complete': True})
        print(repo['ojhamb_runtongy_sgullett_zybu.linkedin'].metadata())

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

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('ojhamb_runtongy_sgullett_zybu', 'ojhamb_runtongy_sgullett_zybu')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont',
                          'http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.

        this_script = doc.agent('alg:ojhamb_runtongy_sgullett_zybu#linkedin',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'], 'ont:Extension': 'py'})

        resource = doc.entity('dat:link_am',
                              {'prov:label': 'Linkedin Data', prov.model.PROV_TYPE: 'ont:DataResource',
                               'ont:Extension': 'json'})
        get_Linkedin = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_Linkedin, this_script)
        doc.usage(get_Linkedin, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval'})
        Linkedin_Data = doc.entity('dat:ojhamb_runtongy_sgullett_zybu#linkedin',
                          {prov.model.PROV_LABEL: 'Linkedin_Data', prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(Linkedin_Data, this_script)
        doc.wasGeneratedBy(Linkedin_Data, get_Linkedin, endTime)
        doc.wasDerivedFrom(Linkedin_Data, resource, get_Linkedin, get_Linkedin, get_Linkedin)

        repo.logout()

        return doc


'''
# This is example code you might use for debugging this module.
# Please remove all top-level function calls before submitting.
'''
'''
linkedin.execute()
doc = linkedin.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))
'''
## eof