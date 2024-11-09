# import dependencies
import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
import ifcopenshell.util.shape


class IFCClient:

    def __init__(self, file):
        print(f'ifcopenshell ver: {ifcopenshell.version}')
        model = ifcopenshell.file()

        # open file
        # file_path = "Kaapelitehdas_junction - Copy.ifc" # default
        self.ifc_file = ifcopenshell.open(file)

    def get_nearby_elements(self, types, coords, radius=3000) -> dict:
        '''
        given a set of coordintates and element types of interest (and an IFC file)
        returns all elements in the a radius around the supplied coordinates
        '''
        elem_info = self.ifc_file.by_type('IfcProduct')
        self.output = {}
        for e in elem_info:
            e_info = e.get_info()
            if e_info['type'] in types:
                # get element location
                matrix = ifcopenshell.util.placement.get_local_placement(e.ObjectPlacement)
                location = (matrix[0][3], matrix[1][3], matrix[2][3])
                # construct sub-dict for element
                e_dict = {}
                e_dict['id'] = e_info['id']
                e_dict['GlobalId'] = e_info['GlobalId']
                e_dict['Name'] = e_info['Name']
                e_dict['type'] = e_info['type']
                e_dict['Description'] = e_info['Description']
                e_dict['location'] = location
                # calculate distance
                distance = ((location[0]-coords[0])**2 + (location[1]-coords[1])**2 + (location[2]-coords[2])**2)**0.5
                if distance <= radius:
                    e_dict['distance'] = distance
                    self.output[e_dict['GlobalId']] = e_dict
        return self.output
    
    def dict_to_string(self, dc):
        '''
        converts the output dict into a string
        '''
        out = ''
        for ke, e in dc.items():
            out += ke + '\n'
            for k, v in e.items():
                out += f'{k:<30}:\t{v}\n'
            out += '\n'
        return out
    
    def update_element_description(self, new_path, globalid, s=None) -> None:
        '''
        updates the description of an element in the IFC file with a given value.
        element is idntified by GlobalID
        '''
        element = self.ifc_file.by_guid(globalid)
        element.Description = s
        updated_path = new_path
        self.ifc_file.write(updated_path)
        pass

    def create_element(self, name, description=None, coordinates=(0,0,0), box_dimensions=(500,500,500)) -> str:
        # set units
        # Define units (e.g., meters)
        units = self.ifc_file.by_type("IfcUnitAssignment")[0] if self.ifc_file.by_type("IfcUnitAssignment") else None

        # Ensure there is a valid IfcGeometricRepresentationContext for "Model"
        geometric_context = self.ifc_file.by_type("IfcGeometricRepresentationContext")
        if not geometric_context:
            # Create a new geometric context if it doesn't exist
            geometric_context = self.ifc_file.create_entity(
                "IfcGeometricRepresentationContext",
                ContextIdentifier="Model",
                ContextType="Model",
                CoordinateSpaceDimension=3,
                Precision=1e-05,
                WorldCoordinateSystem=self.ifc_file.create_entity("IfcAxis2Placement3D")
            )
        else:
            # Use the existing context if found
            geometric_context = geometric_context[0]

        # Get or create the first building storey
        building_storey = self.ifc_file.by_type("IfcBuildingStorey")
        if not building_storey:
            raise ValueError("No IfcBuildingStorey found in IFC file.")
        building_storey = building_storey[0]

        # Create a new IfcBuildingElementProxy as the asset
        new_global_id = ifcopenshell.guid.new()
        proxy = self.ifc_file.create_entity(
            "IfcBuildingElementProxy",
            GlobalId=new_global_id,
            Name= name,
            Description= description,
            ObjectPlacement=None,  # We will assign this next
            Representation=None
        )
        # Create the IfcCartesianPoint at specified coordinates
        location_point = self.ifc_file.create_entity("IfcCartesianPoint", Coordinates=coordinates)
        # Create IfcAxis2Placement3D to define the asset's placement
        placement_3d = self.ifc_file.create_entity("IfcAxis2Placement3D", Location=location_point)
        # Create IfcLocalPlacement to attach the placement to the asset
        local_placement = self.ifc_file.create_entity("IfcLocalPlacement", RelativePlacement=placement_3d)
        proxy.ObjectPlacement = local_placement

        # define extrusion direction
        extrusion_direction = self.ifc_file.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0])
        # Define the box profile (width and height as per box_dimensions)
        width, depth, height = box_dimensions
        rectangle_profile = self.ifc_file.create_entity(
            "IfcRectangleProfileDef",
            ProfileType="AREA",
            XDim=width,
            YDim=depth
        )
        # Define an extrusion of the rectangle profile to create a 3D box
        extruded_area_solid = self.ifc_file.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=rectangle_profile,
            Position=placement_3d,
            ExtrudedDirection=extrusion_direction,
            Depth=height
        )
        # Create an IfcShapeRepresentation to make the box visible
        shape_representation = self.ifc_file.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=self.ifc_file.by_type("IfcGeometricRepresentationContext")[0],
            RepresentationIdentifier="Body",
            RepresentationType="Brep",
            Items=[extruded_area_solid]
        )
        # Assign the shape representation to the proxy
        proxy.Representation = self.ifc_file.create_entity(
            "IfcProductDefinitionShape",
            Representations=[shape_representation]
        )

        # Get the building or site to which the new asset will be attached
        building = self.ifc_file.by_type("IfcBuilding")[0]  # Assumes there is one building in the file
        if not building:
            raise ValueError("No IfcBuilding found in IFC file.")
        # Retrieve the decomposition, convert to list, add proxy, then reassign
        decomposition = list(building.IsDecomposedBy)
        if decomposition:
            related_objects = list(decomposition[0].RelatedObjects)
            related_objects.append(proxy)
            decomposition[0].RelatedObjects = related_objects  # Reassign the modified list back
        else:
            print("No decomposition relationship found.")
        # Save the changes to a new file
        new_ifc_path = "Kaapelitehdas_junction - Beans.ifc"
        self.ifc_file.write(new_ifc_path)
        print(f"New asset '{name}' created at {coordinates} and saved as {new_ifc_path}")
        return new_global_id

# test scripts
#update_element_description(ifc_file, 'Kaapelitehdas_junction - Copy.ifc','1j2wvsYE1C1RNLlNa$rUSe', None)

# new_guid = create_element(ifc_file, 'ShittyBox2', None, [-67000.0,-65000.0,4105.0], (30000,30000,10000))

# new_ifc = ifcopenshell.open("Kaapelitehdas_junction - Beans.ifc")

# all_stuff = get_nearby_elements(new_ifc, ['IfcBuildingElementProxy', 'IfcDoor'], [-67000,-65000,4105])
# for ke, e in all_stuff.items():
#     print(f'### {ke} ###')
#     for k,v in e.items():
#         print(f'{k:<30}:\t{v}')
#     print('')

'''
types = []
# print all walls
for wall in ifc_file.by_type('IfcProduct'):
    wall_info = wall.get_info()
    # discard spaces
    unwanted = ['IfcBuildingStorey', 'IfcSite', 'IfcSpace', 'IfcWallStandardCase', 'IfcOpeningElement', 'IfcBuilding']
    # log all unique types

    if wall_info['type'] in unwanted:
        continue
    if not(wall_info['type'] in types):
        types.append(wall_info['type'])
    # get object location
    matrix = ifcopenshell.util.placement.get_local_placement(wall.ObjectPlacement)
    location = (matrix[0][3], matrix[1][3], matrix[2][3])
    for k, v in wall_info.items():
        print(f'{k:<30}:\t{v}')
    print(f'{"location":<30}:\t{location}\n')
print(types)
'''