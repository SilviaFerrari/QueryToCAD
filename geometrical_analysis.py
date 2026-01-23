import cadquery as cq

# function to analyze the object to determine if it's valid
def analyze_geometry(cq_object):
    
    total_volume = 0
    total_faces = 0
    
    try:
        obj_to_analyze = []
        
        # checking whether cq_object it's a workplane or not 
        if isinstance(cq_object, cq.Workplane):
            # extracts the list of actual solid objects from the container
            obj_to_analyze = cq_object.vals() 
        else:
            # if it's not a workplane, we assume that it's a geometric object
            obj_to_analyze = [cq_object] 

        for obj in obj_to_analyze:

            # checking and calculating the total volume
            if hasattr(obj, "Volume"):
                obj_vol = obj.Volume()
                total_volume += obj_vol

            # checking and calculating the number of faces
            if hasattr(obj, "Faces"):
                obj_faces = len(obj.Faces())
                total_faces += obj_faces
        
    except Exception as e:
        print(f"An error occurred during the geometrical analysis: {e}")
        return {"volume": 0, "faces": 0}

    return {
        "volume": total_volume, 
        "faces": total_faces
    }