'''
Created on June 21, 2011

@author: onesaidwho
'''


from neo4py import models


class PlantModel(models.NodeModel):
    scientific_name = models.StringProperty(index_fulltext=True)
    lifeform = models.StringProperty(min_length=4, max_length=20, index=True)
    region = models.StringProperty(index_icase=True, blank=True, default="")
    endangered = models.BooleanProperty(default=False)
    average_height = models.FloatProperty(min=0, null=True)