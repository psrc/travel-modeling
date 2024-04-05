import arcpy
import sys, string, os


class Toolbox(object):
    def __init__(self):
        self.label =  "Network Tools"
        self.alias  = "network tools"

        # List of tool classes associated with this toolbox
        self.tools = [CalculateSinuosity] 

class Update_IJ(object):
    def __init__(self):
        self.label       = "Updating I & J Nodes."
        self.description = "Edges and Projects have I and J nodes that are defined " + \
                           "by the correspoding junction at the end point of each segment. " + \
                           "Inode is the first node in the sketch and Jnode is the last."

    def getParameterInfo(self):
        #Define parameter definitions

        # Input Features parameter
        in_lines = arcpy.Parameter(
            displayName="Input Lines",
            name="in_lines",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        in_lines.filter.list = ["Polyline"]

         # Input Features parameter
        in_points = arcpy.Parameter(
            displayName="Input Points",
            name="in_points",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        in_points.filter.list = ["Points"]

        # Sinuosity Field parameter
        inode_field = arcpy.Parameter(
            displayName="INode Field",
            name="inode_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        inode_field.value = 'Inode'
        #param1.filter.list = ['Short', 'Long']
        #inode_field.parameterDependencies = [in_lines.name]
        
        
        
        # Derived Output Features parameter
        # Sinuosity Field parameter
        jnode_field = arcpy.Parameter(
            displayName="JNode Field",
            name="jnode_field",
            datatype="Field",
            parameterType="Required",
            direction="Input")
        jnode_field.value = 'Jnode'
        #param1.filter.list = ['Short', 'Long']
        #jnode_field.parameterDependencies = [in_lines.name]
        
    
        parameters = [in_lines, in_points, inode_field, jnode_field]
        
        return parameters

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        if parameters[0].altered:
            parameters[2].value = arcpy.ValidateFieldName(parameters[2].value,
                                                          parameters[0].value)
            parameters[3].value = arcpy.ValidateFieldName(parameters[3].value,
                                                          parameters[0].value)
            
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        line_fc  = parameters[0].valueAsText
        point_fc   = parameters[1].valueAsText
        inode_field = parameters[2].valueAsText
        jnode_field = parameters[3].valueAsText

        arcpy.MakeFeatureLayer_management(line_fc, "line_layer")
        
        lyrDesc = arcpy.da.Describe('line_layer')
        workspace = '\\'.join(lyrDesc["path"].split('\\')[:-1])
        edit = arcpy.da.Editor(workspace)
        edit.startEditing(False, True)
        edit.startOperation()
        
        #lineRows = arcpy.da.UpdateCursor("line_layer", [inode_field, jnode_field])
        #lineRows = arcpy.UpdateCursor("line_layer")

        #lineRows = arcpy.UpdateCursor(line_fc)
        #lineRows = arcpy.UpdateCursor("line_layer")

                                          
        #lineRow = lineRows.next()
        # Edit each Line

        arcpy.MakeFeatureLayer_management(point_fc, "points_lyr")
        with arcpy.da.UpdateCursor("line_layer", ['Shape@', inode_field, jnode_field, "OID@"]) as lineRows:
            for lineRow in lineRows:
            # Get the Line geometry
                from_point = lineRow[0].firstPoint
                point_geom = arcpy.PointGeometry(from_point)
                arcpy.SelectLayerByLocation_management("points_lyr", "CONTAINS", point_geom)
                if int(arcpy.GetCount_management('points_lyr')[0]) == 1:
                    junction_id = arcpy.da.SearchCursor("points_lyr", "PSRCjunctID").next()[0]
                    if junction_id != lineRow[1]:
                        lineRow[1] = junction_id
                        lineRows.updateRow(lineRow)
                else:

                    lineRow[1] = 0
                    lineRows.updateRow(lineRow)
                    arcpy.AddWarning(f"Could not find Inode for ObjectID {lineRow[3]}")

                to_point = lineRow[0].lastPoint
                point_geom = arcpy.PointGeometry(to_point)
                arcpy.SelectLayerByLocation_management("points_lyr", "CONTAINS", point_geom)
                if int(arcpy.GetCount_management('points_lyr')[0]) == 1: 
                    junction_id = arcpy.da.SearchCursor("points_lyr", "PSRCjunctID").next()[0]
                    if junction_id != lineRow[2]:
                        lineRow[2] = junction_id
                        lineRows.updateRow(lineRow)
                else:
                    lineRow[2] = 0
                    lineRows.updateRow(lineRow)
                    arcpy.AddWarning(f"Could not find Jnode for ObjectID {lineRow[3]}")

                #lineRow = lineRows.next()
            edit.stopOperation()

    # Stop the edit session and save the changes
        edit.stopEditing(save_changes=True)
        del lineRows
        del lineRow
        arcpy.AddMessage("Finished")
        
       

    def postExecute(self, parameters):
        return