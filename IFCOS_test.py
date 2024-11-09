# import dependencies
import numpy as np

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
import ifcopenshell.util.shape

print(f'ifcopenshell ver: {ifcopenshell.version}')
model = ifcopenshell.file()

def get_nearby_elements(ifc, types, coords, radius=3000) -> dict:
    '''
    given a set of coordintates and element types of interest (and an IFC file)
    returns all elements in the a radius around the supplied coordinates
    '''
    elem_info = ifc.by_type('IfcProduct')
    output = {}
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
            e_dict['ObjectType'] = e_info['ObjectType']
            e_dict['Description'] = e_info['Description']
            e_dict['location'] = location
            # calculate distance
            distance = ((location[0]-coords[0])**2 + (location[1]-coords[1])**2 + (location[2]-coords[2])**2)**0.5
            if distance <= radius:
                e_dict['distance'] = distance
                output[e_dict['GlobalId']] = e_dict
    return output

def update_element_description(ifc, new_path, globalid, s=None) -> None:
    '''
    updates the description of an element in the IFC file with a given value.
    element is idntified by GlobalID
    '''
    element = ifc.by_guid(globalid)
    element.Description = s
    updated_path = new_path
    ifc.write(updated_path)
    pass

def create_element(ifc, name, path, description=None, coordinates=(0,0,0), box_dimensions=(500,500,500)) -> str:
    # set units
    # Define units (e.g., meters)
    units = ifc.by_type("IfcUnitAssignment")[0] if ifc.by_type("IfcUnitAssignment") else None

    # Ensure there is a valid IfcGeometricRepresentationContext for "Model"
    geometric_context = ifc_file.by_type("IfcGeometricRepresentationContext")
    if not geometric_context:
        # Create a new geometric context if it doesn't exist
        geometric_context = ifc_file.create_entity(
            "IfcGeometricRepresentationContext",
            ContextIdentifier="Model",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1e-05,
            WorldCoordinateSystem=ifc_file.create_entity("IfcAxis2Placement3D")
        )
    else:
        # Use the existing context if found
        geometric_context = geometric_context[1]

    # Set up OwnerHistory if not present
    owner_history = ifc_file.by_type("IfcOwnerHistory")
    if not owner_history:
        application = ifc_file.create_entity(
            "IfcApplication",
            ApplicationDeveloper=ifc_file.create_entity("IfcOrganization", Name="YourOrganization"),
            ApplicationFullName="YourApplicationName",
            ApplicationIdentifier="1234"
        )
        owner_history = ifc_file.create_entity(
            "IfcOwnerHistory",
            OwningApplication=application,
            State=".NOCHANGE."
        )

    # Get or create the first building storey
    building_storey = ifc_file.by_type("IfcBuildingStorey")
    if not building_storey:
        raise ValueError("No IfcBuildingStorey found in IFC file.")
    building_storey = building_storey[0]

    # Create a new IfcBuildingElementProxy as the asset
    new_global_id = ifcopenshell.guid.new()
    proxy = ifc_file.create_entity(
        "IfcBuildingElementProxy",
        GlobalId=new_global_id,
        Name= name,
        ObjectType='Specialty_Equipment_Lift_Assembly:13_Person-Deep_Car',
        Description= description,
        ObjectPlacement=None,  # We will assign this next
        Representation=None
    )
    # Create the IfcCartesianPoint at specified coordinates
    location_point = ifc_file.create_entity("IfcCartesianPoint", Coordinates=coordinates)
    # Create IfcAxis2Placement3D to define the asset's placement
    placement_3d = ifc_file.create_entity("IfcAxis2Placement3D", Location=location_point)
    # Create IfcLocalPlacement to attach the placement to the asset
    local_placement = ifc_file.create_entity("IfcLocalPlacement", PlacementRelTo=building_storey.ObjectPlacement, RelativePlacement=placement_3d)
    proxy.ObjectPlacement = local_placement

    # define extrusion direction
    extrusion_direction = ifc_file.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0])
    # Define the box profile (width and height as per box_dimensions)
    width, depth, height = box_dimensions
    rectangle_profile = ifc_file.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        XDim=width,
        YDim=depth
    )
    # Define an extrusion of the rectangle profile to create a 3D box
    extruded_area_solid = ifc_file.create_entity(
        "IfcExtrudedAreaSolid",
        SweptArea=rectangle_profile,
        Position=placement_3d,
        ExtrudedDirection=extrusion_direction,
        Depth=height
    )
    # Create an IfcShapeRepresentation to make the box visible
    shape_representation = ifc_file.create_entity(
        "IfcShapeRepresentation",
        ContextOfItems=ifc_file.by_type("IfcGeometricRepresentationContext")[0],
        RepresentationIdentifier="Body",
        RepresentationType="Brep",
        Items=[extruded_area_solid]
    )
    # Assign the shape representation to the proxy
    proxy.Representation = ifc_file.create_entity(
        "IfcProductDefinitionShape",
        Representations=[shape_representation]
    )

    # Get the building or site to which the new asset will be attached
    building = ifc_file.by_type("IfcBuilding")[0]  # Assumes there is one building in the file
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
    ifc.write(path)
    print(f"New asset '{name}' created at {coordinates} and saved as {path}")
    return new_global_id

def copy_and_move_element(ifc_file_path, global_id, new_coordinates):
    # Open the IFC file
    ifc_file = ifcopenshell.open(ifc_file_path)

    # Find the original element by its GlobalId
    original_element = ifc_file.by_guid(global_id)
    if not original_element:
        raise ValueError(f"Element with GlobalId {global_id} not found in IFC file.")

    # Copy attributes from the original element
    new_global_id = ifcopenshell.guid.new()
    new_element = ifc_file.create_entity(
        original_element.is_a(),
        GlobalId=new_global_id,
        OwnerHistory=original_element.OwnerHistory,
        Name=f"{original_element.Name}_copy",
        Description=original_element.Description,
        ObjectType=original_element.ObjectType,
        Tag=f"{original_element.Tag}_copy" if original_element.Tag else None,
    )

    # Create new placement for the copied element
    location_point = ifc_file.create_entity("IfcCartesianPoint", Coordinates=new_coordinates)
    placement_3d = ifc_file.create_entity("IfcAxis2Placement3D", Location=location_point)
    new_local_placement = ifc_file.create_entity("IfcLocalPlacement", RelativePlacement=placement_3d)
    new_element.ObjectPlacement = new_local_placement

    # Copy the representation (geometry) of the original element
    new_element.Representation = original_element.Representation

    # Attach the new element to the same spatial structure as the original
    spatial_structure = next(
        rel for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure") if original_element in rel.RelatedElements
    )
    ifc_file.create_entity(
        "IfcRelContainedInSpatialStructure",
        GlobalId=ifcopenshell.guid.new(),
        RelatingStructure=spatial_structure.RelatingStructure,
        RelatedElements=[new_element]
    )

    # Save the updated IFC file
    new_ifc_path = "Kaapelitehdas_junction - Beans.ifc"
    ifc_file.write(new_ifc_path)
    print(f"Copied element with GlobalId {global_id} to new coordinates {new_coordinates}. Saved as {new_ifc_path}.")

    return new_global_id

# test scripts

# open file
file_path = "Kaapelitehdas_junction - Copy.ifc"
ifc_file = ifcopenshell.open(file_path)

'''
types = []
# print all walls
for wall in ifc_file.by_type('IfcProduct'):
    wall_info = wall.get_info()
    # discard spaces
    unwanted = ['IfcBuildingStorey', 'IfcSite', 'IfcSpace', 'IfcWallStandardCase', 'IfcOpeningElement', 'IfcBuilding', 'IfcDoor']
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



update_element_description(ifc_file, 'Kaapelitehdas_junction - Copy.ifc','1j2wvsYE1C1RNLlNa$rUSe', 'Last inspection: 12 Jan 2022')

#new_guid = create_element(ifc_file, 'Fire Extinguisher', "Kaapelitehdas_junction - Copy.ifc", None, [-67135.7847985646, -65276.0128872394, 0.0], (300,300,100))

#new_guid = copy_and_move_element("Kaapelitehdas_junction - Beans.ifc", '1j2wvsYE1C1RNLlNa$rUSe', [-67000.0,-65000.0,4105.0])

#new_ifc = ifcopenshell.open("Kaapelitehdas_junction - Beans.ifc")

all_stuff = get_nearby_elements(ifc_file, ['IfcBuildingElementProxy', 'IfcDoor'], [-67000,-65000,4105], radius=3000)
for ke, e in all_stuff.items():
    print(f'### {ke} ###')
    for k,v in e.items():
        print(f'{k:<30}:\t{v}')
    print('')
